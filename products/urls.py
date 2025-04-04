from django.urls import path

from . import views

urlpatterns = [
    path('about/', views.aboutus_view, name='about_us'),

    path('feeds/', views.feeds_view, name='feeds'),
    path('services/', views.services_view, name='services'),
    path('broiler/', views.broiler_view, name='broiler'),
    path('layers/', views.layers_view, name='layers'),
    path('kienyeji/', views.kienyeji_view, name='kienyeji'),
    path('upload_product/', views.upload_product, name='upload_product'),
]
