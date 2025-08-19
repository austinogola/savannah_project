from django.urls import path,include
from . import views

urlpatterns = [
     # Home page
    path('', views.home_view, name='home'),
    path('home/', views.home_view, name='home'),

    path("login/", views.login_view, name="login"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    

    path('buy/<int:product_id>/', views.buy_product, name='buy-product'),

    # Customer endpoints
    path('customer/', views.CustomerDetailView.as_view(), name='customer-detail'),
    
    # Category endpoints
    path('categories/', views.CategoryListCreateView.as_view(), name='category-list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('categories/<int:category_id>/average-price/', views.category_average_price, name='category-average-price'),
    
    # Product endpoints
    # path('products/', views.ProductListCreateView.as_view(), name='product-list'),
    # path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('products/', views.products_view, name='product-list'),
    # path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path("products/<int:product_id>/order/", views.order_product, name="order_product"),
    
    # Order endpoints
    path("orders/", views.orders_view, name="orders"),
    # path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('orders/create/', views.create_order, name='create-order'),
     path('oidc/', include('mozilla_django_oidc.urls')),
]