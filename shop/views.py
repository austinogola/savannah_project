from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Avg, Q
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from decimal import Decimal
import uuid
from .models import Customer, Category, Product, Order, OrderItem
from .serializers import (
    CustomerSerializer, CategorySerializer, ProductSerializer, 
    OrderSerializer, CreateOrderSerializer
)
from django.template import loader
from django.http import HttpResponse
from django.shortcuts import render
from .models import Product
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .forms import CustomerPhoneForm
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json



class CustomerDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        customer, created = Customer.objects.get_or_create(user=self.request.user)
        return customer


class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def category_average_price(request, category_id):
    """Return the average product price for a given category and its subcategories"""
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return Response(
            {'error': 'Category not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    # Get all descendant categories (including the category itself)
    descendant_categories = category.get_descendants(include_self=True)
    
    # Calculate average price for products in this category tree
    average_price = Product.objects.filter(
        category__in=descendant_categories,
        is_active=True
    ).aggregate(avg_price=Avg('price'))['avg_price']

    if average_price is None:
        average_price = Decimal('0.00')

    return Response({
        'category_id': category_id,
        'category_name': category.name,
        'category_path': category.full_path,
        'average_price': round(average_price, 2),
        'products_count': Product.objects.filter(
            category__in=descendant_categories,
            is_active=True
        ).count()
    })


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        customer = Customer.objects.get_or_create(user=self.request.user)[0]
        return Order.objects.filter(customer=customer).order_by('-created_at')


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        customer = Customer.objects.get_or_create(user=self.request.user)[0]
        return Order.objects.filter(customer=customer)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_order(request):
    """Create a new order with items"""
    serializer = CreateOrderSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Get or create customer
    customer, created = Customer.objects.get_or_create(user=request.user)

    # Create order
    order = Order.objects.create(
        customer=customer,
        order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
        shipping_address=serializer.validated_data['shipping_address'],
        notes=serializer.validated_data.get('notes', '')
    )

    # Create order items
    total_amount = Decimal('0.00')
    for item_data in serializer.validated_data['items']:
        product = Product.objects.get(id=item_data['product_id'])
        quantity = int(item_data['quantity'])
        
        # Check stock
        if product.stock_quantity < quantity:
            return Response(
                {'error': f'Insufficient stock for {product.name}. Available: {product.stock_quantity}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            unit_price=product.price
        )
        total_amount += order_item.subtotal
        
        # Update stock
        product.stock_quantity -= quantity
        product.save()

    # Update order total
    order.total_amount = total_amount
    order.save()

    return Response(
        OrderSerializer(order).data, 
        status=status.HTTP_201_CREATED
    )


def products_view(request):
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()

    # --- Filtering ---
    category_id = request.GET.get("category")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")

    if category_id:
        category = get_object_or_404(Category, id=category_id)
        # include selected category + all descendants
        category_ids = category.get_descendants(include_self=True).values_list("id", flat=True)
        products = products.filter(category_id__in=category_ids)

    if min_price:
        try:
            products = products.filter(price__gte=Decimal(min_price))
        except:
            pass

    if max_price:
        try:
            products = products.filter(price__lte=Decimal(max_price))
        except:
            pass

    context = {
        "products": products,
        "categories": categories,
    }
    return render(request, "products.html", context)
    
def products_view2(request):
    if request.user.is_authenticated:
        # user is logged in
        ...
        print('User is logged in')
    else:
        # user is anonymous
        ...
        print('User is logged NOT LOGGEDin')
    # products = Product.objects.filter(is_active=True)
    products_qs = Product.objects.filter(is_active=True)
    products = list(products_qs) if products_qs.exists() else []  # ensure plain list or []
    return render(request, "products.html", {"products": products })

def home_view(request):
    if request.user.is_authenticated:
        # user is logged in
        ...
        print('User is logged in')
    else:
        # user is anonymous
        ...
        print('User is logged NOT LOGGEDin')
    # products = Product.objects.filter(is_active=True)
    products_qs = Product.objects.filter(is_active=True)
    products = list(products_qs) if products_qs.exists() else []  # ensure plain list or []
    return render(request, "home.html", {"products": products })

@login_required
def buy_product(request, product_id):
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id, is_active=True)

        # get or create the Customer record for this user
        customer, created = Customer.objects.get_or_create(user=request.user)

        # get or create an open order for this user (you can choose if you want multiple orders or one open at a time)
        order = Order.objects.create(customer=customer, total_amount=0)

        # add product to order
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,  # for now, always 1 (can add form input later)
            unit_price=product.price
        )

        # update total
        order.total_amount = product.price
        order.save()

        messages.success(request, f"{product.name} added to your order!")
        return redirect("home")

    return redirect("home")


@login_required
def order_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)

    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))
        customer = request.user.customer  # from your Customer model

        # create new order
        order = Order.objects.create(customer=customer)
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            unit_price=product.price,
        )
        order.calculate_total()
        messages.success(request, f"{product.name} added to your order!")

        return redirect("orders")  # redirect to orders page

    return redirect("products")



def login_view(request):
    # If already authenticated, go home
    if request.user.is_authenticated:
        return redirect("/shop/dashboard")
    return render(request, "login.html")


@login_required
def dashboard_view(request):
    customer, created = Customer.objects.get_or_create(user=request.user)
    print('customer',customer)
    print('user',request.user)
    # customer = request.user.customer  # access your Customer model
        # Get last 5 orders of the logged-in user
    recent_orders = Order.objects.filter(customer=customer).order_by('-created_at')[:5]

    # Get some products (you can customize this later)
    products = Product.objects.filter(is_active=True)[:5]

    context = {
        "recent_orders": recent_orders,
        "products": products
    }
    return render(request, "dashboard.html", {"context": context})




@login_required
def orders_view(request):
    orders = Order.objects.all()

    print('all orders',orders)
    for order in orders:
        print(f"Order ID: {order.id}")
        print(f"Customer: {order.customer}")
        print(f"Status: {order.status}")
        print(f"Total: {order.total_amount}")
        print(f"Created At: {order.created_at}")
        print("------")
    print(request.user)

    # Filter by status
    status = request.GET.get('status')
    print('status',status)
    if status and status != "all":
        print('Getting for all statuses')
        orders = orders.filter(status=status)

    # Filter by date range
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    if start_date:
        orders = orders.filter(created_at__gte=parse_date(start_date))
    if end_date:
        orders = orders.filter(created_at__lte=parse_date(end_date))

    return render(request, "orders.html", {"orders": orders})



@login_required
def collect_phone(request):
    print('HERE NOW')
    
    customer, created = Customer.objects.get_or_create(user=request.user)

    user = request.user

    usertype = request.session.pop("usertype", "normal")
    print('usertype',usertype)
    if usertype == "admin":
        user.is_staff = True
        user.is_superuser = True
        user.save()
    else:
        user.is_staff = False
        user.is_superuser = False
        user.save() 
    # Populate first and last name if missing
        # Example: set first_name and last_name if not already set
    if not user.first_name or not user.last_name:
        # Try to fetch from OpenID info, e.g., from session
        print('no names')
        oidc_info = request.session.get('oidc_userinfo', {})
        print('oidc_info',oidc_info)
        user.first_name = oidc_info.get('given_name', '')
        user.last_name = oidc_info.get('family_name', '')
        print('first_name',oidc_info.get('given_name'))
        user.save()
    
    print(customer.phone, created)
    print(user, created)
    
    if customer.phone:
        return redirect('/shop/dashboard')
    
    if request.method == 'POST':
        form = CustomerPhoneForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('/shop/dashboard')
    else:
        form = CustomerPhoneForm(instance=customer)
    
    return render(request, 'collect_phone.html', {'form': form})


def logout_view(request):
    logout(request)  # Logs out the user from Django
    return redirect('/shop')  



@csrf_exempt
def set_usertype(request):
    if request.method == "POST":
        data = json.loads(request.body)
        usertype = data.get("usertype", "normal")
        request.session["usertype"] = usertype
        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "Invalid method"}, status=400)