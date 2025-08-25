# shop/tests/conftest.py
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from shop.models import Category, Product, Customer

@pytest.fixture()
def client():
    return APIClient()

@pytest.fixture()
def category():
    return Category.objects.create(name="Electronics")

@pytest.fixture()
def product(category):
    return Product.objects.create(
        name="Phone", price="699.00", category=category, stock_quantity=10
    )

@pytest.fixture()
def user():
    return User.objects.create_user(username="u1", password="pass", first_name="Ada")

@pytest.fixture()
def customer(user):
    return Customer.objects.create(user=user, phone="+254700000000")
