from rest_framework import serializers
from .models import Customer, Category, Product, Order, OrderItem
from decimal import Decimal


class CustomerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'phone', 'created_at']


class CategorySerializer(serializers.ModelSerializer):
    full_path = serializers.ReadOnlyField()
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'parent', 'full_path', 
                 'children_count', 'created_at', 'updated_at']

    def get_children_count(self, obj):
        return obj.get_children().count()


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_path = serializers.CharField(source='category.full_path', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category', 
                 'category_name', 'category_path', 'stock_quantity', 'is_active', 
                 'created_at', 'updated_at']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.user.get_full_name', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_number', 'customer', 'customer_name', 'status', 
                 'total_amount', 'items', 
                 'created_at', 'updated_at']
        read_only_fields = ['order_number', 'total_amount']


class CreateOrderSerializer(serializers.Serializer):
    # shipping_address = serializers.CharField()
    # notes = serializers.CharField(required=False, allow_blank=True)
    items = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must contain at least one item.")
        
        for item in value:
            if 'product_id' not in item or 'quantity' not in item:
                raise serializers.ValidationError(
                    "Each item must have 'product_id' and 'quantity'."
                )
            try:
                product_id = int(item['product_id'])
                quantity = int(item['quantity'])
                if quantity <= 0:
                    raise serializers.ValidationError("Quantity must be positive.")
                # Verify product exists
                Product.objects.get(id=product_id, is_active=True)
            except (ValueError, Product.DoesNotExist):
                raise serializers.ValidationError(f"Invalid product or quantity.")
        
        return value
