from django.contrib import admin
from django.urls import path, include
from apps.empleados.views import *

app_name='root'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('generar/<int:id>/', generar_carnet, name='generar'),
    path('renderizar/', renderizar, name='renderizar'),
    path('generar/imprimir/<int:cedula>/', imprimir, name='imprimir'),
    
]
