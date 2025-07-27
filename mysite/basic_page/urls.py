from django.urls import path
from .views import HomePageView, TopstonePageView, ProductionPageView, DeliveryPageView, InstallationPageView, \
    StairsPageView, SinksPageView, SillsPageView, DimensionsPageTemplate, PolitiConfPageTemplate, \
    PanelsPageTemplates, BarPageTemplates, FireplacePageTemplate, QuartzStonePageView, AcrylStonePageTemplate, \
    NaturalStonePageTemplate, PorcelainStonePageTemplate, ReceptionPageTemplate, SelectionStonePageTemplate, \
    contacts, choice_stone, SendUsPageTemplate, export_ceramics_view, export_natural_view, \
    export_acrylic_view, export_quartz_view, export_userbids_view, export_panel_view

app_name = 'basic_page'

urlpatterns = [
    path('', HomePageView.as_view(), name='main_page'),
    path('main', HomePageView.as_view(), name='main_page_2'),
    path('main_page', HomePageView.as_view(), name='main_page_2'),
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
    path('quartz', QuartzStonePageView.as_view(), name='quartz'),
    path('acryl', AcrylStonePageTemplate.as_view(), name='acryl'),
    path('natural', NaturalStonePageTemplate.as_view(), name='natural'),
    path('porcelain', PorcelainStonePageTemplate.as_view(), name='porcelain'),
    path('reception', ReceptionPageTemplate.as_view(), name='reception'),
    path('selection', SelectionStonePageTemplate.as_view(), name='selection'),
    path('otheracrylstone', SelectionStonePageTemplate.as_view(), name='otheracrylstone'),
    path('other', SelectionStonePageTemplate.as_view(), name='other'),
    path('choice', choice_stone, name='choice'),
    path('trend/hopetoun', choice_stone, name='media'),
    path('about', contacts, name='about'),
    path('partner', SendUsPageTemplate.as_view(), name='partner'),
    path('calculator', contacts, name='calculator'),
    path('zamer', contacts, name='zamer'),
    #export views ↓
    path('PsstFuVvwLjdQvu', export_ceramics_view, name='export_ceramics_view'),
    path('t3WNStJaz2N5Cuw', export_natural_view, name='export_natural_view'),
    path('pnCne7xcIVMjG57', export_acrylic_view, name='export_acrylic_view'),
    path('Nor2qRjFD3wbKiy', export_quartz_view, name='export_quartz_view'),
    path('X5KD08OHn25yNLf', export_userbids_view, name='export_userbids_view'),
    path('export_panel', export_panel_view, name="export_panel_view"),
]
