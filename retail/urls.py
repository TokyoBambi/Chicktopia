from django.urls import path

from . import views

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('update_cart/', views.update_cart, name='update_cart'),
    # Order URLs
    path('orders/', views.order_list, name='order_list'),
    path('orders/<uuid:order_id>/', views.order_detail, name='order_detail'),
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/<uuid:order_id>/update/',
         views.update_order, name='update_order'),
    path('orders/<uuid:order_id>/delete/',
         views.delete_order, name='delete_order'),
    path('order_success/', views.order_success, name='order_success'),

    # Payment URLs
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/<uuid:payment_id>/',
         views.payment_detail, name='payment_detail'),
    path('orders/<uuid:order_id>/payment/create/',
         views.create_payment, name='create_payment'),
    path('payments/<uuid:payment_id>/update/',
         views.update_payment, name='update_payment'),
    # Sale URLs
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/<uuid:sale_id>/', views.sale_detail, name='sale_detail'),
    path('sales/create/', views.create_sale, name='create_sale'),
    path('sales/<uuid:sale_id>/update/', views.update_sale, name='update_sale'),
    path('sales/<uuid:sale_id>/delete/', views.delete_sale, name='delete_sale'),
    path('create_order_from_cart/', views.create_order_from_cart,
         name='create_order_from_cart'),
    path('create_payment/<uuid:order_id>/',
         views.create_payment, name='create_payment'),
    path('create_sale/<uuid:order_id>/', views.create_sale, name='create_sale'),
]
