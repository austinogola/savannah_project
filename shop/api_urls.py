from django.urls import path
from . import api_views

urlpatterns = [
    # Categories
    path("categories/", api_views.CategoryListCreateView.as_view(), name="category-list-create"),
    path("categories/<int:pk>/", api_views.CategoryDetailView.as_view(), name="category-detail"),
    path("categories/<int:pk>/avg-price/", api_views.CategoryAvgPriceView.as_view(), name="category-avg-price"),

    # Products
    path("products/", api_views.ProductListCreateView.as_view(), name="product-list-create"),
    # path("products/", api_views.ProductListCreateView.as_view(), name="product-list"),  # GET (list w/ filters), POST (create)


    # Customers
    path("customers/", api_views.CustomerListCreateView.as_view(), name="customer-list-create"),
    # Customers
    # path("customers/", api_views.CustomerListCreateView.as_view(), name="customer-list"),  # GET (list w/ filters), POST (create)


    # Users
    path("users/", api_views.UserCreateView.as_view(), name="user-create"),

    # Orders
    path("orders/", api_views.OrderCreateView.as_view(), name="order-create"),
]


