"""
URL configuration for Capstone project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path
from core import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('main', views.main, name='Pagina Principal'),
    path('perfil', views.perfil, name='perfil'),
    path('residentes', views.residentes, name='Residentes'),
    path('crear', views.crear_residente, name='crear Residente'),
    path('eliminacion_residente/<id>', views.eliminar_residente, name='eliminar Residente'),
    path('edicion_residente/<id>', views.edicion_residente, name='edicion Residente'),
    path('autos', views.autos, name='autos'),
    path('crearAuto', views.crear_auto, name='crear Auto'),
    path('eliminacion_auto/<id>', views.eliminar_auto, name='eliminar Auto'),
    path('edicion_auto/<id>', views.edicion_auto, name='edicion Auto'),
    path('video_feed', views.video_feed, name='video_feed'),
    path('', views.inicioSesion, name='/'),
    path('cerrarSesion', views.cerrarSesion, name="cerrarSesion"),
    path('verificar_patente_detectada/', views.verificar_patente_detectada, name='verificar_patente_detectada'),    
    path('reconocedor/', views.reconocedor, name='reconocedor'),
    path('informes/', views.informes, name='informes'),
    path('upload/', views.upload_excel, name='upload_excel'),
    # Si deseas aceptar una fecha, puedes agregar otro patrón de URL
    path('informes/<str:fecha_dia>/', views.informes, name='informes_con_fecha'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)