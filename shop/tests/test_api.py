import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from shop.models import Category, Product, Customer, Order, OrderItem

@pytest.fixture()
def client():
    return APIClient()

@pytest.fixture()
def category():
    return Category.objects.create(name="Electronics")

@pytest.fixture()
def product(category):
    return Product.objects.create(name="Phone", price="699.00", category=category, stock_quantity=10)

@pytest.fixture()
def user():
    return User.objects.create_user(username="u1", password="pass", first_name="Ada")

@pytest.fixture()
def customer(user):
    return Customer.objects.create(user=user, phone="+254700000000")
@pytest.mark.django_db
def test_category_list_create(client):
    # list
    url = reverse("category-list-create")
    r = client.get(url)
    assert r.status_code == 200
    # create
    r = client.post(url, {"name": "Books"}, format="json")
    assert r.status_code in (200, 201)
    assert Category.objects.filter(name="Books").exists()
@pytest.mark.django_db
def test_product_list_filter(client, category, product):
    url = reverse("product-list-create")
    assert client.get(url).status_code == 200
    assert client.get(url + f"?category_id={category.id}").status_code == 200
    assert client.get(url + f"?category_name={category.name}").status_code == 200
@pytest.mark.django_db
def test_create_product(client, category):
    url = reverse("product-list-create")
    r = client.post(url, {"name": "Laptop", "price": "1000.00", "category_id": category.id}, format="json")
    assert r.status_code in (200, 201)
    assert Product.objects.filter(name="Laptop").exists()
@pytest.mark.django_db
def test_customer_list_create(client, user):
    url = reverse("customer-list-create")
    # list
    assert client.get(url).status_code == 200
    # create
    r = client.post(url, {"user": user.id, "phone": "+254711111111"}, format="json")
    assert r.status_code in (200, 201)
    assert Customer.objects.filter(user=user).exists()
@pytest.mark.django_db
def test_user_create_creates_customer(client):
    url = reverse("user-create")
    data = {
    "username": "neo",
    "first_name": "Neo",
    "last_name": "Smith",
     "phone": "+254722222222",
    "email": "example@email.com",   # if serializer requires it
    }
    data={"username": "neo", "first_name": "Neo", "phone": "+254722222222", "password": "testpass123"}
    r = client.post(url, data, format="json")
    assert r.status_code in (200, 201)
    assert User.objects.filter(username="neo").exists()
    u = User.objects.get(username="neo")
    assert Customer.objects.filter(user=u).exists()
@pytest.mark.django_db
def test_order_create(client, customer, product):
    url = reverse("order-create")
    data = {"customer_id": customer.id, "items": [{"product_id": product.id, "quantity": 2}]}
    r = client.post(url, data, format="json")
    assert r.status_code in (200, 201)
    order = Order.objects.get(customer=customer)
    assert order.items.count() == 1
    assert float(order.total_amount) == 2 * float(product.price)
