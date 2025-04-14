from django.contrib import admin
from .models import Order, OrderItem, Payment, Sale


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ['product', 'quantity', 'get_total']
    readonly_fields = ['get_total']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'date_ordered',
                    'status', 'total_amount', 'get_items_count']
    list_filter = ['status', 'date_ordered']
    search_fields = ['id', 'user__username', 'user__email', 'phone_number']
    readonly_fields = ['id', 'date_ordered',
                       'get_order_total', 'get_items_count']
    date_hierarchy = 'date_ordered'
    inlines = [OrderItemInline]
    list_per_page = 20

    fieldsets = (
        ('Order Information', {
            'fields': ('id', 'user', 'date_ordered', 'status')
        }),
        ('Financial Details', {
            'fields': ('total_amount', 'get_order_total')
        }),
        ('Customer Details', {
            'fields': ('shipping_address', 'phone_number', 'notes')
        }),
    )

    def get_items_count(self, obj):
        return obj.get_items_count
    get_items_count.short_description = 'Items Count'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'quantity', 'get_total']
    list_filter = ['order__status']
    search_fields = ['order__id', 'product__title']
    readonly_fields = ['get_total']

    def get_total(self, obj):
        return obj.get_total
    get_total.short_description = 'Total'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'payment_method',
                    'amount_paid', 'status', 'payment_date']
    list_filter = ['payment_method', 'status', 'payment_date']
    search_fields = ['id', 'order__id', 'transaction_id']
    readonly_fields = ['id', 'payment_date']
    date_hierarchy = 'payment_date'

    fieldsets = (
        ('Payment Information', {
            'fields': ('id', 'order', 'payment_method', 'status')
        }),
        ('Financial Details', {
            'fields': ('amount_paid', 'transaction_id', 'payment_date')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ['order',]
        return self.readonly_fields


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'customer',
                    'sale_date', 'total_amount', 'profit']
    list_filter = ['sale_date']
    search_fields = ['id', 'order__id', 'customer__user__username']
    readonly_fields = ['id']
    date_hierarchy = 'sale_date'
    filter_horizontal = ['products']

    fieldsets = (
        ('Sale Information', {
            'fields': ('id', 'order', 'customer', 'sale_date')
        }),
        ('Products', {
            'fields': ('products',)
        }),
        ('Financial Details', {
            'fields': ('total_amount', 'profit')
        }),
    )
