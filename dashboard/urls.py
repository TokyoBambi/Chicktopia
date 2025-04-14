from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name="dashboard"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('services/', views.services_view, name='services'),
    path('about_us/', views.about_us_view, name='about_us'),
]
