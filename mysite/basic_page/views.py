from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
# from .mixins import AdminDashboard
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from .forms import UserBidForm
from catalog.models import QuartzStone, AcrylicStone, NaturalStone, CeramicsStone
from .utils.table_export import export_stones, export_userbids

class HomePageView(TemplateView):
    template_name = 'basic_page/front/page45356997.html'


class TopstonePageView(TemplateView):
    template_name = 'basic_page/front/page45645015.html'


class ProductionPageView(TemplateView):
    template_name = 'basic_page/front/page46621539.html'


class DeliveryPageView(TemplateView):
    template_name = 'basic_page/front/page46646809.html'


class QuartzStonePageView(TemplateView):
    template_name = 'basic_page/front/page46666977.html'


class InstallationPageView(TemplateView):
    template_name = 'basic_page/front/page46653351.html'


class StairsPageView(TemplateView):
    template_name = 'basic_page/front/page45773985.html'


class SinksPageView(TemplateView):
    template_name = 'basic_page/front/page45773669.html'


class SillsPageView(TemplateView):
    template_name = 'basic_page/front/page45773539.html'


class DimensionsPageTemplate(TemplateView):
    template_name = 'basic_page/front/page45758267.html'


class PolitiConfPageTemplate(TemplateView):
    template_name = 'basic_page/front/page48434273.html'


class PanelsPageTemplates(TemplateView):
    template_name = 'basic_page/front/page48013929.html'


class BarPageTemplates(TemplateView):
    template_name = 'basic_page/front/page48014037.html'


class FireplacePageTemplate(TemplateView):
    template_name = 'basic_page/front/page48014045.html'


class AcrylStonePageTemplate(TemplateView):
    template_name = 'basic_page/front/page45670875.html'


class NaturalStonePageTemplate(TemplateView):
    template_name = 'basic_page/front/page48527563.html'


class PorcelainStonePageTemplate(TemplateView):
    template_name = 'basic_page/front/page48525119.html'


class ReceptionPageTemplate(TemplateView):
    template_name = 'basic_page/front/page48014075.html'


class SelectionStonePageTemplate(TemplateView):
    template_name = 'basic_page/front/page45643781.html'


def _save_user_bid(request):
    form = UserBidForm(request.POST)
    if form.is_valid():
        form.save()
        return None
    return form


def _form_errors_response(form):
    return JsonResponse(
        {
            'status': 'error',
            'message': 'Проверьте заполнение формы.',
            'errors': form.errors.get_json_data(),
        },
        status=400,
    )
def choice_stone(request):
    if request.method == 'POST':
        form = _save_user_bid(request)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            if form is None:
                return JsonResponse({'status': 'success'})
            return _form_errors_response(form)
        if form is not None:
            return render(request, 'basic_page/front/page45107597.html', {'form': form}, status=400)
    return render(request, 'basic_page/front/page45107597.html')
class TrendsStonePageTemplate(TemplateView):
    template_name = 'basic_page/front/page45068325.html'

class SendUsPageTemplate(TemplateView):
    template_name = 'basic_page/send_us.html'

def contacts(request):
    if request.method == 'POST':
        form = _save_user_bid(request)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            if form is None:
                return JsonResponse({'status': 'success'})
            return _form_errors_response(form)
        if form is not None:
            return render(request, 'basic_page/contacts.html', {'form': form}, status=400)

    return render(request, 'basic_page/contacts.html')
@staff_member_required
def export_quartz_view(request):
    return export_stones(request, QuartzStone, 'quartz_stones', 'Кварцевые камни')

@staff_member_required
def export_acrylic_view(request):
    return export_stones(request, AcrylicStone, 'acrylic_stones', 'Акриловые камни')

@staff_member_required
def export_natural_view(request):
    return export_stones(request, NaturalStone, 'natural_stones', 'Природные камни')

@staff_member_required
def export_ceramics_view(request):
    return export_stones(request, CeramicsStone, 'ceramics_stones', 'Керамические камни')

@staff_member_required
def export_userbids_view(request):
    wb = export_userbids(request)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="user_requests.xlsx"'

    wb.save(response)
    return response

@staff_member_required
def export_panel_view(request):
    return render(request, 'basic_page/export_panel.html')
