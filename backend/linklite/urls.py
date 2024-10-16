from django.urls import path

from . import views


app_name = 'linklite'

urlpatterns = [
    path('s/<str:url_hash>/', views.take_url, name='take_url'),
]
