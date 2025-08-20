from django.contrib.auth.models import User
from django.db.models import Avg
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Product, Category, Customer, Order, OrderItem
from .api_serializers import (
    ProductSerializer, CustomerSerializer, UserSerializer,
    CategorySerializer, OrderSerializer
)
from .views import send_confirmation_messages

# -------- Categories --------
class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CategoryDetailView(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CategoryAvgPriceView(APIView):
    def get(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

        products = Category.get_products_for_category(category.id)
        avg_price = products.aggregate(avg=Avg("price"))["avg"]
        return Response({"category": category.name, "average_price": avg_price})


# -------- Products --------
# class ProductListCreateView(APIView):
#     def get(self, request):
#         queryset = Product.objects.all()

#         category_id = request.query_params.get("category_id")
#         category_name = request.query_params.get("category_name")

#         if category_id:
#             queryset = queryset.filter(category_id=category_id)
#         if category_name:
#             queryset = queryset.filter(category__name__iexact=category_name)

#         serializer = ProductSerializer(queryset, many=True)
#         return Response(serializer.data)

#     def post(self, request):
#         serializer = ProductSerializer(data=request.data)
#         if serializer.is_valid():
#             product = serializer.save()
#             return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class ProductListCreateView(generics.ListCreateAPIView):
    """
    GET: List all products (optionally filter by category_id or category_name).
    POST: Create a new product.
    """
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    def get_queryset(self):
        queryset = Product.objects.all()
        category_id = self.request.query_params.get("category_id")
        category_name = self.request.query_params.get("category_name")

        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if category_name:
            queryset = queryset.filter(category__name__iexact=category_name)

        return queryset

# -------- Customers --------
# class CustomerListCreateView(generics.ListCreateAPIView):
#     queryset = Customer.objects.all()
#     serializer_class = CustomerSerializer

#     def get_queryset(self):
#         queryset = Customer.objects.all()
#         phone = self.request.query_params.get("phone")
#         user_id = self.request.query_params.get("user_id")

#         if phone:
#             queryset = queryset.filter(phone__icontains=phone)
#         if user_id:
#             queryset = queryset.filter(user_id=user_id)

#         return queryset
class CustomerListCreateView(generics.ListCreateAPIView):
    """
    GET: List all customers (filterable by phone or user_id).
    POST: Create a new customer.
    """
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        phone = self.request.query_params.get("phone")
        user_id = self.request.query_params.get("user_id")

        if phone:
            queryset = queryset.filter(phone__icontains=phone)
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        return queryset


# -------- Users --------
# class UserCreateView(APIView):
#     def post(self, request):
#         phone = request.data.get("phone")
#         first_name = request.data.get("first_name")
#         last_name = request.data.get("last_name")

#         if not phone:
#             return Response({"error": "Phone is required"}, status=status.HTTP_400_BAD_REQUEST)
#         if not (first_name or last_name):
#             return Response({"error": "At least first_name or last_name is required"}, status=status.HTTP_400_BAD_REQUEST)

#         serializer = UserSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save()
#             Customer.objects.create(user=user, phone=phone)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class UserCreateView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()  # serializer handles Customer creation
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# -------- Orders --------
class OrderCreateView(APIView):
    def post(self, request):
        customer_id = request.data.get("customer_id")
        items = request.data.get("items")

        if not items:
            return Response({"error": "Items are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)

        order = Order.objects.create(customer=customer)

        for item in items:
            product_id = item.get("product_id")
            quantity = int(item.get("quantity", 1))
            try:
                product = Product.objects.get(pk=product_id)
            except Product.DoesNotExist:
                return Response({"error": f"Product {product_id} not found"}, status=status.HTTP_404_NOT_FOUND)

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=product.price
            )

        order.calculate_total()
        serializer = OrderSerializer(order)
        messages_results=send_confirmation_messages(customer=customer,user=customer.user,order=order,product=product,quantity=quantity)
        
        return Response({"order":serializer.data,"confirmation_messages":messages_results}, status=status.HTTP_201_CREATED)
