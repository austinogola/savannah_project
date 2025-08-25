from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import logout
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal

from .models import Product, Category, Customer, Order, OrderItem
from .forms import CustomerPhoneForm
import json

from django.core.mail import send_mail
from django.contrib.auth.models import User
from .services import sendmail,sendText
from django.views.generic import TemplateView

def home_view(request):
    products = Product.objects.filter(is_active=True)[:10]
    print(products)
    return render(request, "home.html", {"products": products})

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


def send_confirmation_messages(customer,user,order,product,quantity):
    
    phone_number = customer.phone  # make sure phone is saved in international format, e.g., +2547xxxxxxx
    print('customer_phone',phone_number)
    text_status=''

    if phone_number:
        message = f"Hello {customer.user.first_name}, your order {order.order_number} for {quantity} x {product.name} totaling ${order.total_amount} has been received. Thank you for shopping with us!"
        text_status = sendText(phone_number=phone_number,message=message)
    else:
        text_status='User has no phone number'

    admin_users = User.objects.filter(is_staff=True, is_active=True)
    admin_emails = [u.email for u in admin_users if u.email]


    # for email in admin_emails:
    subject = f"New Order Placed: {order.order_number}"
    message = f"""
    Hello Admin,

    A new order has been placed:

    Customer: {user.get_full_name()} ({customer.phone})
    Product: {product.name}
    Quantity: {quantity}
    Total: ${order.total_amount}
    Text Status: {text_status}

    Please review the order in the dashboard.
    """
    mail_res=sendmail(subject=subject,message=message,fromEmail='info@austino.online',toEmails=admin_emails)
        # print(mail_res)

    return({'confirmation_text_status':text_status,'admin_email_status':mail_res})


@login_required
def order_product(request, product_id):
    # 1. Ensure product exists and is active
    product = get_object_or_404(Product, id=product_id, is_active=True)

    # 2. Ensure user exists (covered by @login_required, but still safe-check)
    user = request.user
    if not user or not user.is_authenticated:
        return HttpResponseForbidden("You must be logged in to order a product.")

    # 3. Ensure customer profile exists
    try:
        customer = user.customer
    except Customer.DoesNotExist:
        return HttpResponseBadRequest("Customer profile is missing. Please create one before ordering.")

    # 4. Handle only POST requests
    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
        except ValueError:
            return HttpResponseBadRequest("Invalid quantity provided.")

        if quantity <= 0:
            return HttpResponseBadRequest("Quantity must be at least 1.")

        # Create order + order item
        order = Order.objects.create(customer=customer)
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            unit_price=product.price,
        )
        order.calculate_total()

        messages.success(request, f"{product.name} added to your order!")

        # Send confirmation messages
        messages_results = send_confirmation_messages(
            customer=customer, user=user, order=order, product=product, quantity=quantity
        )
        print("messages_results", messages_results)

        return redirect("orders")

    # If not POST → redirect
    return redirect("products")



@login_required
def orders_view(request):
    orders = Order.objects.all()

    status = request.GET.get("status")
    if status and status != "all":
        orders = orders.filter(status=status)

    start_date = request.GET.get("start")
    end_date = request.GET.get("end")
    if start_date:
        orders = orders.filter(created_at__gte=start_date)
    if end_date:
        orders = orders.filter(created_at__lte=end_date)

    return render(request, "orders.html", {"orders": orders})


@login_required
def collect_phone(request):
    customer, _ = Customer.objects.get_or_create(user=request.user)
    user = request.user

    usertype = request.session.get("usertype","normal")
    print('usertype',usertype)
    user.is_staff = usertype == "admin"
    user.is_superuser = usertype == "admin"
    user.save()

    if not user.first_name or not user.last_name:
        oidc_info = request.session.get("oidc_userinfo", {})
        user.first_name = oidc_info.get("given_name", "")
        user.last_name = oidc_info.get("family_name", "")
        user.save()

    if customer.phone:
        return redirect("/shop/dashboard")

    if request.method == "POST":
        form = CustomerPhoneForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect("/shop/dashboard")
    else:
        form = CustomerPhoneForm(instance=customer)

    return render(request, "collect_phone.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("/shop/dashboard")
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("/shop")


@csrf_exempt
def set_usertype(request):
    if request.method == "POST":
        data = json.loads(request.body)
        request.session["usertype"] = data.get("usertype", "normal")
        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "Invalid method"}, status=400)



class DocsView(TemplateView):
    template_name = "docs.html"