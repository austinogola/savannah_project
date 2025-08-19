# shop/api_urls.py
from django.urls import path
from .api_views import (
    ProductBulkUploadView, ProductCreateView,
    category_average_price_api, CreateOrderView,CategoryListAPIView
)

urlpatterns = [
    path("products/", ProductCreateView.as_view(), name="api-product-create"),
    path("products/bulk/", ProductBulkUploadView.as_view(), name="api-product-bulk"),
    path("categories/<int:category_id>/average-price/", category_average_price_api, name="api-category-average-price"),
    path("orders/", CreateOrderView.as_view(), name="api-create-order"),
    path("categories/", CategoryListAPIView.as_view(), name="api-categories-list"),
]