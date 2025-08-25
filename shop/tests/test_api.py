# shop/tests/test_api.py
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from shop.models import Category, Product, Customer, Order

# ---------- Categories ----------
@pytest.mark.django_db
def test_category_list_create(client):
    url = reverse("category-list-create")
    # list
    assert client.get(url).status_code == 200
    # create
    r = client.post(url, {"name": "Books"}, format="json")
    assert r.status_code == 201
    assert Category.objects.filter(name="Books").exists()

@pytest.mark.django_db
def test_category_create_with_parent_by_name(client, category):
    url = reverse("category-list-create")
    r = client.post(url, {"name": "Laptops", "parent": category.name}, format="json")
    assert r.status_code == 201
    assert Category.objects.filter(name="Laptops", parent=category).exists()

@pytest.mark.django_db
def test_category_detail(client, category):
    url = reverse("category-detail", args=[category.id])
    r = client.get(url)
    assert r.status_code == 200
    assert r.data["id"] == category.id

@pytest.mark.django_db
def test_category_avg_price(client, category, product):
    url = reverse("category-avg-price", args=[category.id])
    r = client.get(url)
    assert r.status_code == 200
    assert "average_price" in r.data

@pytest.mark.django_db
def test_category_avg_price_invalid(client):
    url = reverse("category-avg-price", args=[999])
    r = client.get(url)
    assert r.status_code == 404

# ---------- Products ----------
@pytest.mark.django_db
def test_product_list_filter(client, category, product):
    url = reverse("product-list-create")
    assert client.get(url).status_code == 200
    assert client.get(url + f"?category_id={category.id}").status_code == 200
    assert client.get(url + f"?category_name={category.name}").status_code == 200

@pytest.mark.django_db
def test_product_create_with_category_id(client, category):
    url = reverse("product-list-create")
    r = client.post(url, {"name": "Laptop", "price": "1000.00", "category_id": category.id}, format="json")
    assert r.status_code == 201
    assert Product.objects.filter(name="Laptop").exists()

@pytest.mark.django_db
def test_product_create_with_category_name(client, category):
    url = reverse("product-list-create")
    r = client.post(url, {"name": "Novel", "price": "10.00", "category_name": category.name}, format="json")
    assert r.status_code == 201
    assert Product.objects.filter(name="Novel").exists()

@pytest.mark.django_db
def test_product_create_invalid_category(client):
    url = reverse("product-list-create")
    r = client.post(url, {"name": "Tablet", "price": "500.00", "category_name": "DoesNotExist"}, format="json")
    assert r.status_code == 400

# ---------- Customers ----------
@pytest.mark.django_db
def test_customer_list_create(client, user):
    url = reverse("customer-list-create")
    assert client.get(url).status_code == 200
    r = client.post(url, {"user": user.id, "phone": "+254711111111"}, format="json")
    assert r.status_code == 201
    assert Customer.objects.filter(user=user).exists()

@pytest.mark.django_db
def test_customer_filter_by_phone(client, customer):
    url = reverse("customer-list-create") + "?phone=2547"
    r = client.get(url)
    assert r.status_code == 200
    assert len(r.data) >= 1

@pytest.mark.django_db
def test_customer_filter_by_user_id(client, customer):
    url = reverse("customer-list-create") + f"?user_id={customer.user.id}"
    r = client.get(url)
    assert r.status_code == 200
    assert len(r.data) == 1

# ---------- Users ----------
@pytest.mark.django_db
def test_user_create_creates_customer(client):
    url = reverse("user-create")
    data = {"username": "neo", "first_name": "Neo", "phone": "+254722222222", "password": "testpass123"}
    r = client.post(url, data, format="json")
    assert r.status_code == 201
    u = User.objects.get(username="neo")
    assert Customer.objects.filter(user=u).exists()

@pytest.mark.django_db
def test_user_create_fails_without_phone(client):
    url = reverse("user-create")
    data = {"username": "no_phone", "first_name": "Test", "password": "pass"}
    r = client.post(url, data, format="json")
    assert r.status_code == 400

# ---------- Orders ----------
@pytest.mark.django_db
def test_order_create(client, customer, product):
    url = reverse("order-create")
    data = {"customer_id": customer.id, "items": [{"product_id": product.id, "quantity": 2}]}
    r = client.post(url, data, format="json")
    assert r.status_code == 201
    order = Order.objects.get(customer=customer)
    assert order.items.count() == 1

@pytest.mark.django_db
def test_order_create_invalid_customer(client, product):
    url = reverse("order-create")
    data = {"customer_id": 999, "items": [{"product_id": product.id, "quantity": 1}]}
    r = client.post(url, data, format="json")
    assert r.status_code == 404

@pytest.mark.django_db
def test_order_create_invalid_product(client, customer):
    url = reverse("order-create")
    data = {"customer_id": customer.id, "items": [{"product_id": 999, "quantity": 1}]}
    r = client.post(url, data, format="json")
    assert r.status_code == 404

@pytest.mark.django_db
def test_order_create_without_items(client, customer):
    url = reverse("order-create")
    data = {"customer_id": customer.id, "items": []}
    r = client.post(url, data, format="json")
    assert r.status_code == 400
