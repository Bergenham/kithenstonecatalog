"""
URL configuration for mysite project.

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
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
import os
from .settings import DEBUG, MEDIA_URL, MEDIA_ROOT

urlpatterns = [
    path('admin/', admin.site.urls),
    path('catalog/', include('catalog.urls')),
    path('', include('basic_page.urls')),
]
if DEBUG:
    # Для обслуживания медиафайлов во время разработки
    from django.conf.urls.static import static
    urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
#___________for all page(without trend)________

urlpatterns += static(
    '/css/',
    document_root=os.path.join(settings.BASE_DIR, 'basic_page/templates/basic_page/front/css')
)

urlpatterns += static(
    '/js/',
    document_root=os.path.join(settings.BASE_DIR, 'basic_page/templates/basic_page/front/js')
)

urlpatterns += static(
    '/images/',
    document_root=os.path.join(settings.BASE_DIR, 'basic_page/templates/basic_page/front/images')
)

#___________only for trend(site page)________
urlpatterns += static(
    'trend/css/',
    document_root=os.path.join(settings.BASE_DIR, 'basic_page/templates/basic_page/front/css')
)

urlpatterns += static(
    'trend/js/',
    document_root=os.path.join(settings.BASE_DIR, 'basic_page/templates/basic_page/front/js')
)

urlpatterns += static(
    'trend/images/',
    document_root=os.path.join(settings.BASE_DIR, 'basic_page/templates/basic_page/front/images')
)
#_______________________________________________
# #___________only for trend(site page)________
urlpatterns += static(
    'catalog/css/',
    document_root=os.path.join(settings.BASE_DIR, 'catalog/templates/fronttemp/css')
)

urlpatterns += static(
    'catalog/js/',
    document_root=os.path.join(settings.BASE_DIR, 'catalog/templates/fronttemp/js')
)

urlpatterns += static(
    'catalog/images/',
    document_root=os.path.join(settings.BASE_DIR, 'catalog/templates/fronttemp/images')
)
#_______________________________________________