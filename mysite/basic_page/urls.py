from django.urls import path
# from .views import (MainPage, StoneSelection, Dimensions,
#                     Production, Delivery, Installation,
#                     Topstone, Sills, Sinks, Stairs
#                     Panels, Bar, Reception,
#                     Fireplace,
#                     )
from .views import HomePageView, TopstonePageView, ProductionPageView, DeliveryPageView, InstallationPageView, \
    StairsPageView, SinksPageView, SillsPageView, DimensionsPageTemplate, PolitiConfPageTemplate, \
    PanelsPageTemplates, BarPageTemplates, FireplacePageTemplate

app_name = 'basic_page'

urlpatterns = [
    path('', HomePageView.as_view(), name='main_page'),
    path('main', HomePageView.as_view(), name='main_page_2'),
    path('topstone', TopstonePageView.as_view(), name='topstone'),
    path('production', ProductionPageView.as_view(), name='productions'),
    path('delivery', DeliveryPageView.as_view(), name='delivery'),
    path('installation', InstallationPageView.as_view(), name='installation'),
    path('stairs', StairsPageView.as_view(), name='stairs'),
    path('sinks', SinksPageView.as_view(), name='sinks'),
    path('sills', SillsPageView.as_view(), name='sills'),
    path('dimensions', DimensionsPageTemplate.as_view(), name='dimensions'),
    path('privacy', PolitiConfPageTemplate.as_view(), name='politic_conf'),
    path('panels', PanelsPageTemplates.as_view(), name='panels'),
    path('bar', BarPageTemplates.as_view(), name='bar'),
    path('fireplace', FireplacePageTemplate.as_view(), name='fireplace'),
]