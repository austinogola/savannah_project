import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from shop.models import Category, Product, Customer

@pytest.fixture()
def client():
    return APIClient()

@pytest.mark.django_db
def test_category_create_with_parent_by_name(client):
    parent = Category.objects.create(name="Electronics")
    url = reverse("category-list-create")
    data = {"name": "Laptops", "parent": "Electronics"}
    r = client.post(url, data, format="json")
    assert r.status_code in (200, 201)
    assert Category.objects.filter(name="Laptops", parent=parent).exists()

@pytest.mark.django_db
def test_product_create_with_category_name(client):
    Category.objects.create(name="Books")
    url = reverse("product-list-create")
    data = {"name": "Novel", "price": "10.00", "category_name": "Books"}
    r = client.post(url, data, format="json")
    assert r.status_code in (200, 201)
    assert Product.objects.filter(name="Novel").exists()

@pytest.mark.django_db
def test_product_create_invalid_category(client):
    url = reverse("product-list-create")
    data = {"name": "Tablet", "price": "500.00", "category_name": "DoesNotExist"}
    r = client.post(url, data, format="json")
    assert r.status_code == 400

@pytest.mark.django_db
def test_user_create_fails_without_phone(client):
    url = reverse("user-create")
    data = {"username": "no_phone", "first_name": "Test", "password": "pass"}
    r = client.post(url, data, format="json")
    assert r.status_code == 400

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
