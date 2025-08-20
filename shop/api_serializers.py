from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Product, Customer, Category, Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):
    parent = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = Category
        fields = ["id", "name", "description", "parent", "full_path", "created_at", "updated_at"]

    def create(self, validated_data):
        parent_value = validated_data.pop("parent", None)
        parent_obj = None
        if parent_value:
            if str(parent_value).isdigit():
                parent_obj = Category.objects.filter(id=int(parent_value)).first()
            else:
                parent_obj = Category.objects.filter(name=parent_value).first()
        category = Category.objects.create(parent=parent_obj, **validated_data)
        return category


# class ProductSerializer(serializers.ModelSerializer):
#     category = serializers.CharField(write_only=True)  # can accept id or name
#     category_detail = CategorySerializer(source="category", read_only=True)

#     class Meta:
#         model = Product
#         fields = ["id", "name", "description", "price", "stock_quantity", "is_active", "category", "category_detail"]

#     def create(self, validated_data):
#         category_value = validated_data.pop("category")
#         category_obj = None
#         if str(category_value).isdigit():
#             category_obj = Category.objects.filter(id=int(category_value)).first()
#         else:
#             category_obj = Category.objects.filter(name=category_value).first()

#         if not category_obj:
#             raise serializers.ValidationError({"category": "Invalid category"})

#         return Product.objects.create(category=category_obj, **validated_data)

class ProductSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(required=False, write_only=True)
    category_name = serializers.CharField(required=False, write_only=True)
    category_detail = CategorySerializer(source="category", read_only=True)

    class Meta:
        model = Product
        fields = (
            "id", "name", "description", "price",
            "stock_quantity", "is_active",
            "category_id", "category_name",  "category_detail"
        )
        read_only_fields = ("category",)

    def create(self, validated_data):
        category_id = validated_data.pop("category_id", None)
        category_name = validated_data.pop("category_name", None)

        category = None
        if category_id:
            category = Category.objects.filter(id=category_id).first()
        elif category_name:
            category = Category.objects.filter(name__iexact=category_name).first()

        if not category:
            raise serializers.ValidationError("Valid category_id or category_name is required.")

        return Product.objects.create(category=category, **validated_data)


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "user", "phone", "address"]


# class UserSerializer(serializers.ModelSerializer):
#     phone = serializers.CharField(write_only=True)

#     class Meta:
#         model = User
#         fields = ["id", "username", "first_name", "last_name", "email", "phone"]
class UserSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True)  # accept phone but don't try to store on User

    class Meta:
        model = User
        fields = ("id", "username", "password", "first_name", "last_name", "phone")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        phone = validated_data.pop("phone")
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        Customer.objects.create(user=user, phone=phone)
        return user

class OrderItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source="product", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["product", "product_detail", "quantity", "unit_price", "subtotal"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "order_number", "customer", "status", "total_amount", "items", "created_at"]
