from django.urls import path
from .views import QuartzCatalog, AcrilCatalog, NaturalCatalog, CeramicCatalog, stone_detail_a, stone_detail_c, stone_detail_n, stone_detail_q
from django.views.defaults import page_not_found

app_name = 'catalog'

urlpatterns = [
    path('quartz', QuartzCatalog.as_view(), name='quartz_catalog'),
    path('acril', AcrilCatalog.as_view(), name='acril_catalog'),
    path('natural', NaturalCatalog.as_view(), name='natural_catalog'),
    path('ceramic', CeramicCatalog.as_view(), name='ceramic_catalog'),
    path('quartz/stone/<int:stone_id>', stone_detail_q, name='stone_detail_q'),
    path('acril/stone/<int:stone_id>', stone_detail_a, name='stone_detail_a'),
    path('natural/stone/<int:stone_id>', stone_detail_n, name='stone_detail_n'),
    path('ceramic/stone/<int:stone_id>', stone_detail_c, name='stone_detail_c'),
]

handler404 = 'myapp.views.custom_404_view'