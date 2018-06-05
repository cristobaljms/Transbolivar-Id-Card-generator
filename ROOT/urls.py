from django.contrib import admin
from django.urls import path, include
from apps.empleados.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index),
]
