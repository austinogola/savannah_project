from django.urls import path, include
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    # Public pages
    path("", views.home_view, name="home"),
    path("home/", views.home_view, name="home"),
    
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Dashboard
    path("dashboard/", views.dashboard_view, name="dashboard"),

    path("collect-phone/", views.collect_phone, name="collect-phone"),

    # Products (web shop)
    path("products/", views.products_view, name="product-list"),
    # path("buy/<int:product_id>/", views.buy_product, name="buy-product"),
     path("products/<int:product_id>/order/", views.order_product, name="order_product"),

    # Orders (web shop)
    path("orders/", views.orders_view, name="orders"),

    # OIDC login
    path("oidc/", include("mozilla_django_oidc.urls")),

    # Misc
    path("set_usertype/", views.set_usertype, name="set_usertype"),

    path("docs/", views.DocsView.as_view(), name="api-docs"),
     path("guide/", TemplateView.as_view(template_name="guide.html"), name="guide"),

]
