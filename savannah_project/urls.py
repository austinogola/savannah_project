"""
URL configuration for savannah_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include,re_path
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.generic import RedirectView

schema_view = get_schema_view(
   openapi.Info(
      title="My API",
      default_version='v1',
      description="Detailed API documentation for all endpoints",
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

def redirect_to_shop_logout(request):
    return redirect('shop:logout') 

urlpatterns = [
    path('admin/', admin.site.urls),

     # root (/) → /shop/
    path("", RedirectView.as_view(url="/shop/", permanent=False)),

    # /home → /shop/
    path("home/", RedirectView.as_view(url="/shop/", permanent=False)),
    # /login → /shop/login
    path("login/", RedirectView.as_view(url="/shop/login/", permanent=False)),


     path('shop/', include('shop.urls')),
    path('oidc/', include('mozilla_django_oidc.urls')),
    
     path("api/", include("shop.api_urls")),
    #  path("logout/", include("shop.urls")),
    path("logout/", redirect_to_shop_logout, name="logout"),
     re_path(r'^docs(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0), name='schema-json'),


            #  path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
