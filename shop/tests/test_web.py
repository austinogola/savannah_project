import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from unittest.mock import patch

from shop import views, services, serializers
from shop.models import Customer, Product, Category, Order, OrderItem
from shop.forms import CustomerPhoneForm
from shop.auth import MyOIDCBackend

pytestmark = pytest.mark.django_db

# ---------- Views ----------

def test_home_view(client, product):
    response = client.get("/") 

    assert response.status_code in (200, 302)

def test_products_view_filters(client, category, product):
    # with no filters
    request = RequestFactory().get("/products/")
    response = views.products_view(request)
    assert response.status_code == 200

    # with min/max filters (valid)
    request = RequestFactory().get("/products/?min_price=100&max_price=1000")
    response = views.products_view(request)
    assert response.status_code == 200

def test_dashboard_view_authenticated(user):
    factory = RequestFactory()
    request = factory.get("/dashboard/")
    request.user = user
    # attach session + messages
    setattr(request, "session", {})
    setattr(request, "_messages", FallbackStorage(request))
    response = views.dashboard_view(request)
    assert response.status_code == 200

def test_buy_product_post(user, product):
    factory = RequestFactory()
    request = factory.post("/buy/")
    request.user = user
    setattr(request, "session", {})
    setattr(request, "_messages", FallbackStorage(request))
    response = views.order_product(request, product.id)
    assert response.status_code == 302  # redirect


def test_customer_phone_form_valid(user):
    form = CustomerPhoneForm(data={"phone": "+254700000000"}, instance=Customer(user=user))
    assert form.is_valid()
# def test_set_usertype_sets_session(client):
#     r = client.post(reverse("set-usertype"), data={"usertype": "admin"}, content_type="application/json")
#     assert r.status_code == 200
#     assert r.json()["status"] == "ok"


# ---------- Services ----------

@patch("shop.services.send_mail", return_value=1)
def test_sendmail_success(mock_send):
    result = services.sendmail("subject", "body", toEmails=["a@b.com"])
    assert result == "Success"

@patch("shop.services.send_mail", side_effect=Exception("fail"))
def test_sendmail_failure(mock_send):
    result = services.sendmail("subject", "body", toEmails=["a@b.com"])
    assert "Failed" in result

@patch("shop.services.africastalking.SMS.send", return_value={"SMSMessageData": {"Recipients":[{"status":"Success"}]}})
@patch("shop.services.africastalking.initialize")
def test_sendText_success(mock_init, mock_send):
    result = services.sendText("+254700000000", "hi")
    assert result == "Success"

@patch("shop.services.africastalking.SMS.send", side_effect=Exception("boom"))
@patch("shop.services.africastalking.initialize")
def test_sendText_failure(mock_init, mock_send):
    result = services.sendText("+254700000000", "hi")
    assert "Failed" in result


# ---------- Serializers ----------

def test_customer_serializer(user, customer):
    s = serializers.CustomerSerializer(customer)
    assert s.data["username"] == user.username

def test_category_serializer_children_count(category):
    s = serializers.CategorySerializer(category)
    assert "children_count" in s.data

def test_product_serializer(product):
    s = serializers.ProductSerializer(product)
    assert s.data["name"] == product.name

def test_order_serializer(customer, product):
    order = Order.objects.create(customer=customer)
    OrderItem.objects.create(order=order, product=product, quantity=1, unit_price=product.price)
    s = serializers.OrderSerializer(order)
    assert "items" in s.data

def test_create_order_serializer_valid(product):
    s = serializers.CreateOrderSerializer(data={"items":[{"product_id": str(product.id), "quantity": "1"}]})
    assert s.is_valid(), s.errors

def test_create_order_serializer_invalid():
    s = serializers.CreateOrderSerializer(data={"items":[{"product_id":"999","quantity":"0"}]})
    assert not s.is_valid()


def test_oidc_update_user(db):
    user = User.objects.create(username="oidc")
    claims = {"given_name": "Ada", "family_name": "Lovelace", "email": "ada@example.com"}
    backend = MyOIDCBackend()
    updated = backend.update_user(user, claims)
    assert updated.first_name == "Ada"
    assert updated.last_name == "Lovelace"
    assert updated.email == "ada@example.com"


# products_view with invalid min_price
def test_products_view_invalid_min_price(client):
    response = client.get("/shop/products/?min_price=notanumber")
    assert response.status_code == 200  # gracefully ignores

# order_product with bad quantity
def test_order_product_invalid_quantity(client, user, product):
    client.force_login(user)
    Customer.objects.create(user=user, phone="+2547...")
    response = client.post(f"/shop/order/{product.id}/", {"quantity": "abc"})
    assert response.status_code == 400



# order_product with GET (should redirect)
def test_order_product_get_redirect(client, user, product):
    client.force_login(user)
    Customer.objects.create(user=user, phone="+2547112233444")
    response = client.get(f"/shop/order/{product.id}/")
    assert response.status_code == 302

# collect_phone - existing phone skips form
def test_collect_phone_existing_phone(client, customer):
    client.force_login(customer.user)
    response = client.get("/shop/collect-phone/")
    assert response.status_code == 302

# collect_phone - POST valid phone
def test_collect_phone_post_valid(client, user):
    client.force_login(user)
    response = client.post("/shop/collect-phone/", {"phone": "+2547112233447"})
    assert response.status_code == 302

# set_usertype - GET method
def test_set_usertype_get(client):
    response = client.get("/shop/set_usertype/")
    assert response.status_code == 400