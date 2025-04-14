from django.urls import path

from . import views

urlpatterns = [
    path('feeds/', views.feeds_view, name='feeds'),
    path('broiler/', views.broiler_view, name='broiler'),
    path('layers/', views.layers_view, name='layers'),
    path('kienyeji/', views.kienyeji_view, name='kienyeji'),
    path('upload_product/', views.upload_product, name='upload_product'),
    path('products/', views.product_list, name='product_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('add_to_cart/<int:product_id>/',
         views.add_to_cart, name='add_to_cart'),
]
