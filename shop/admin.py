from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from .models import Customer, Category, Product, Order, OrderItem


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone')


@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    search_fields = ('name',)
    mptt_level_indent = 20


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock_quantity', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'is_active')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('subtotal',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'customer__user__username')
    inlines = [OrderItemInline]
