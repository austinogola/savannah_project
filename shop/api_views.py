# shop/api_views.py
from decimal import Decimal
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status, permissions, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import Category, Product, Order, OrderItem, Customer
from mptt.exceptions import InvalidMove
from django.db.models import Avg

# ---------- Helpers ----------

def get_or_create_category_by_path(path: str) -> Category:
    """
    path like: "Bakery > Bread > Sourdough" OR "Bakery/Bread/Sourdough"
    Creates intermediate nodes if missing.
    """
    if not path:
        raise serializers.ValidationError("category_path is required.")
    parts = [p.strip() for p in path.replace("/", ">").split(">") if p.strip()]
    parent = None
    current = None
    for name in parts:
        current, _ = Category.objects.get_or_create(name=name, parent=parent)
        parent = current
    return current


# ---------- Serializers ----------

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description", "parent"]

class ProductSerializer(serializers.ModelSerializer):
    category_full_path = serializers.CharField(source="category.full_path", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "description", "price", "category", "category_full_path",
                  "stock_quantity", "is_active", "created_at", "updated_at"]

class ProductUploadSerializer(serializers.Serializer):
    """
    Upload a single product. Choose one:
      - category (id)  OR
      - category_path (string like 'Parent > Child')
    """
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(allow_blank=True, required=False)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = serializers.IntegerField(min_value=0, default=100)
    is_active = serializers.BooleanField(default=True)

    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False)
    category_path = serializers.CharField(required=False)

    def validate(self, attrs):
        if not attrs.get("category") and not attrs.get("category_path"):
            raise serializers.ValidationError("Provide either 'category' or 'category_path'.")
        return attrs

    def create(self, validated):
        category = validated.get("category")
        if not category:
            category = get_or_create_category_by_path(validated.pop("category_path"))
        return Product.objects.create(category=category, **validated)

class BulkProductUploadSerializer(serializers.Serializer):
    products = ProductUploadSerializer(many=True)

    def create(self, validated):
        created = []
        with transaction.atomic():
            for pdata in validated["products"]:
                created.append(ProductUploadSerializer().create(pdata))
        return created

class OrderItemInSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

class CreateOrderSerializer(serializers.Serializer):
    items = OrderItemInSerializer(many=True)

    def validate(self, attrs):
        # validate product existence and stock
        items = attrs["items"]
        product_ids = [i["product_id"] for i in items]
        products = {p.id: p for p in Product.objects.filter(id__in=product_ids, is_active=True)}
        for item in items:
            p = products.get(item["product_id"])
            if not p:
                raise serializers.ValidationError(f"Product {item['product_id']} not found/active.")
            if p.stock_quantity < item["quantity"]:
                raise serializers.ValidationError(
                    f"Insufficient stock for {p.name}. Available: {p.stock_quantity}"
                )
        attrs["_products"] = products
        return attrs

    def create(self, validated, *, customer: Customer) -> Order:
        products = validated["_products"]
        items = validated["items"]

        with transaction.atomic():
            order = Order.objects.create(customer=customer)
            total = Decimal("0.00")
            for item in items:
                p = products[item["product_id"]]
                qty = int(item["quantity"])
                OrderItem.objects.create(
                    order=order,
                    product=p,
                    quantity=qty,
                    unit_price=p.price,
                )
                total += p.price * qty
                # reduce stock
                p.stock_quantity -= qty
                p.save(update_fields=["stock_quantity"])
            order.total_amount = total
            order.save(update_fields=["total_amount"])
        return order

class OrderItemOutSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    subtotal = serializers.SerializerMethodField()

    def get_subtotal(self, obj):
        return obj.subtotal

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "quantity", "unit_price", "subtotal"]

class OrderOutSerializer(serializers.ModelSerializer):
    items = OrderItemOutSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "order_number", "status", "total_amount", "created_at", "items"]


# ---------- Endpoints ----------

class ProductBulkUploadView(generics.CreateAPIView):
    """
    POST /api/products/bulk/
    {
      "products": [
        {"name":"Sourdough","price":"4.99","stock_quantity":50,"category_path":"Bakery > Bread"},
        {"name":"Bagel","price":"1.50","category": 12}
      ]
    }
    """
    serializer_class = BulkProductUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        created = ser.save()
        return Response(ProductSerializer(created, many=True).data, status=status.HTTP_201_CREATED)


class ProductCreateView(generics.CreateAPIView):
    """
    POST /api/products/
    Single product upload (same fields as ProductUploadSerializer)
    """
    serializer_class = ProductUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        product = ser.create(ser.validated_data)
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])  # make it public if you like
def category_average_price_api(request, category_id: int):
    """
    GET /api/categories/<id>/average-price/
    Includes all descendants of the category.
    """
    category = get_object_or_404(Category, id=category_id)
    descendants = category.get_descendants(include_self=True)
    avg_price = (
        Product.objects.filter(is_active=True, category__in=descendants)
        .aggregate(avg=Avg("price"))["avg"]
        or Decimal("0.00")
    )
    return Response(
        {
            "category_id": category.id,
            "category_name": category.name,
            "category_path": category.full_path,
            "average_price": round(Decimal(avg_price), 2),
            "products_count": Product.objects.filter(is_active=True, category__in=descendants).count(),
        }
    )


class CreateOrderView(generics.CreateAPIView):
    """
    POST /api/orders/
    {
      "items": [
        {"product_id": 5, "quantity": 2},
        {"product_id": 9, "quantity": 1}
      ]
    }
    """
    serializer_class = CreateOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        # ensure the Customer exists for this user
        customer, _ = Customer.objects.get_or_create(user=request.user)
        order = ser.create(ser.validated_data, customer=customer)
        return Response(OrderOutSerializer(order).data, status=status.HTTP_201_CREATED)

class CategoryListAPIView(generics.ListAPIView):
    """
    GET /api/categories/
    Returns all categories with id, name, parent id, and full path
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]  # Public endpoint