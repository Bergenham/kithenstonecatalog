from django.core.exceptions import ValidationError
from django.views.generic import ListView
from .models import QuartzStone, StoneImage, CeramicsStone, AcrylicStone, NaturalStone
from django.shortcuts import render, get_object_or_404, redirect, reverse, HttpResponse
from django.http import JsonResponse
from basic_page.models import UserBidModel
from django.http import HttpResponseNotFound
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.db.models import Count

def custom_404_view(request, exception):
    return HttpResponseNotFound(render(request, 'fronttemp/404.html'))

def stone_detail_q(request, stone_id=None):
    if stone_id:
        stone = get_object_or_404(QuartzStone.objects.filter(archive=False), pk=stone_id)
        images = StoneImage.objects.filter(stone=stone).all()
    else:
        return redirect(reverse("basic_page:main"))

    if request.method == 'POST':
        response_data = {'status': 'error', 'message': ''}

        try:
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            email = request.POST.get('email', '').strip()


            UserBidModel.objects.create(
                full_name=full_name,
                phone=phone,
                email=email,
            )
            response_data = {'status': 'success'}

        except ValidationError as e:
            response_data['message'] = str(e)
        except Exception as e:
            response_data['message'] = "Ошибка сервера: " + str(e)

        return JsonResponse(response_data)

    return render(request, 'fronttemp/about_stone.html', {
        'stone': stone,
        'img_m': images,
    })

def stone_detail_c(request, stone_id=None):
    if stone_id:
        stone = get_object_or_404(CeramicsStone.objects.filter(archive=False), pk=stone_id)
        images = StoneImage.objects.filter(stone=stone, archive=False).all()
    else:
        return redirect(reverse("basic_page:main"))

    if request.method == 'POST':
        response_data = {'status': 'error', 'message': ''}

        try:
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            email = request.POST.get('email', '').strip()


            UserBidModel.objects.create(
                full_name=full_name,
                phone=phone,
                email=email,
            )
            response_data = {'status': 'success'}

        except ValidationError as e:
            response_data['message'] = str(e)
        except Exception as e:
            response_data['message'] = "Ошибка сервера: " + str(e)

        return JsonResponse(response_data)

    return render(request, 'fronttemp/about_stone.html', {
        'stone': stone,
        'img_m': images,
    })

def stone_detail_a(request, stone_id=None):
    if stone_id:
        stone = get_object_or_404(AcrylicStone.objects.filter(archive=False), pk=stone_id)
        images = StoneImage.objects.filter(stone=stone, archive=False).all()
    else:
        return redirect(reverse("basic_page:main"))

    if request.method == 'POST':
        response_data = {'status': 'error', 'message': ''}

        try:
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            email = request.POST.get('email', '').strip()


            UserBidModel.objects.create(
                full_name=full_name,
                phone=phone,
                email=email,
            )
            response_data = {'status': 'success'}

        except ValidationError as e:
            response_data['message'] = str(e)
        except Exception as e:
            response_data['message'] = "Ошибка сервера: " + str(e)

        return JsonResponse(response_data)

    return render(request, 'fronttemp/about_stone.html', {
        'stone': stone,
        'img_m': images,
    })

def stone_detail_n(request, stone_id=None):
    if stone_id:
        stone = get_object_or_404(NaturalStone.objects.filter(archive=False), pk=stone_id)
        images = StoneImage.objects.filter(stone=stone, archive=False).all()
    else:
        return redirect(reverse("basic_page:main"))

    if request.method == 'POST':
        response_data = {'status': 'error', 'message': ''}

        try:
            full_name = request.POST.get('full_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            email = request.POST.get('email', '').strip()


            UserBidModel.objects.create(
                full_name=full_name,
                phone=phone,
                email=email,
            )
            response_data = {'status': 'success'}

        except ValidationError as e:
            response_data['message'] = str(e)
        except Exception as e:
            response_data['message'] = "Ошибка сервера: " + str(e)

        return JsonResponse(response_data)

    return render(request, 'fronttemp/about_stone.html', {
        'stone': stone,
        'img_m': images,
    })

class QuartzCatalog(ListView):
    template_name = 'fronttemp/quartz_catalog.html'
    context_object_name = 'stones'
    ordering = ['name_stone']
    paginate_by = None \

    def get_queryset(self):
        queryset = QuartzStone.objects.filter(archive=False).only(
            'name_stone',
            'priview_img',
            'brand_stone',
            'color',
            'texture',
            'faktura',
        )

        brand = self.request.GET.getlist('brand')
        color = self.request.GET.getlist('color')
        texture = self.request.GET.getlist('texture')
        faktura = self.request.GET.getlist('faktura')

        if brand:
            queryset = queryset.filter(brand_stone__in=brand)
        if color:
            queryset = queryset.filter(color__in=color)
        if texture:
            queryset = queryset.filter(texture__in=texture)
        if faktura:
            queryset = queryset.filter(faktura__in=faktura)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['selected_brands'] = self.request.GET.getlist('brand')
        context['selected_colors'] = self.request.GET.getlist('color')
        context['selected_textures'] = self.request.GET.getlist('texture')
        context['selected_fakturas'] = self.request.GET.getlist('faktura')

        stones_qs = QuartzStone.objects.filter(archive=False)
        context['brand_options'] = list(
            stones_qs.order_by('brand_stone').values_list('brand_stone', flat=True).distinct()
        )
        context['color_options'] = list(
            stones_qs.order_by('color').values_list('color', flat=True).distinct()
        )
        context['texture_options'] = list(
            stones_qs.order_by('texture').values_list('texture', flat=True).distinct()
        )
        context['faktura_options'] = list(
            stones_qs.order_by('faktura').values_list('faktura', flat=True).distinct()
        )

        return context

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('fronttemp/_stones_grid.html', context, request=request)
            return HttpResponse(html)

        return self.render_to_response(context)


class CeramicCatalog(ListView):
    template_name = 'fronttemp/ceramic_catalog.html'
    context_object_name = 'stones'
    ordering = ['name_stone']
    paginate_by = None \

    def get_queryset(self):
        queryset = CeramicsStone.objects.filter(archive=False).only(
            'name_stone',
            'priview_img',
            'brand_stone',
            'color',
            'texture',
            'faktura',
        )

        brand = self.request.GET.getlist('brand')
        color = self.request.GET.getlist('color')
        texture = self.request.GET.getlist('texture')
        faktura = self.request.GET.getlist('faktura')

        if brand:
            queryset = queryset.filter(brand_stone__in=brand)
        if color:
            queryset = queryset.filter(color__in=color)
        if texture:
            queryset = queryset.filter(texture__in=texture)
        if faktura:
            queryset = queryset.filter(faktura__in=faktura)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['selected_brands'] = self.request.GET.getlist('brand')
        context['selected_colors'] = self.request.GET.getlist('color')
        context['selected_textures'] = self.request.GET.getlist('texture')
        context['selected_fakturas'] = self.request.GET.getlist('faktura')

        stones_qs = CeramicsStone.objects.filter(archive=False)
        context['brand_options'] = list(
            stones_qs.order_by('brand_stone').values_list('brand_stone', flat=True).distinct()
        )
        context['color_options'] = list(
            stones_qs.order_by('color').values_list('color', flat=True).distinct()
        )
        context['texture_options'] = list(
            stones_qs.order_by('texture').values_list('texture', flat=True).distinct()
        )
        context['faktura_options'] = list(
            stones_qs.order_by('faktura').values_list('faktura', flat=True).distinct()
        )

        return context

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('fronttemp/_stones_grid.html', context, request=request)
            return HttpResponse(html)

        return self.render_to_response(context)

class NaturalCatalog(ListView):
    template_name = 'fronttemp/natural_catalog.html'
    context_object_name = 'stones'
    ordering = ['name_stone']
    paginate_by = None \

    def get_queryset(self):
        queryset = NaturalStone.objects.filter(archive=False).only(
            'name_stone',
            'priview_img',
            'brand_stone',
            'color',
            'texture',
            'faktura',
        )

        brand = self.request.GET.getlist('brand')
        color = self.request.GET.getlist('color')
        texture = self.request.GET.getlist('texture')
        faktura = self.request.GET.getlist('faktura')

        if brand:
            queryset = queryset.filter(brand_stone__in=brand)
        if color:
            queryset = queryset.filter(color__in=color)
        if texture:
            queryset = queryset.filter(texture__in=texture)
        if faktura:
            queryset = queryset.filter(faktura__in=faktura)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['selected_brands'] = self.request.GET.getlist('brand')
        context['selected_colors'] = self.request.GET.getlist('color')
        context['selected_textures'] = self.request.GET.getlist('texture')
        context['selected_fakturas'] = self.request.GET.getlist('faktura')

        stones_qs = NaturalStone.objects.filter(archive=False)
        context['brand_options'] = list(
            stones_qs.order_by('brand_stone').values_list('brand_stone', flat=True).distinct()
        )
        context['color_options'] = list(
            stones_qs.order_by('color').values_list('color', flat=True).distinct()
        )
        context['texture_options'] = list(
            stones_qs.order_by('texture').values_list('texture', flat=True).distinct()
        )
        context['faktura_options'] = list(
            stones_qs.order_by('faktura').values_list('faktura', flat=True).distinct()
        )

        return context

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('fronttemp/_stones_grid.html', context, request=request)
            return HttpResponse(html)

        return self.render_to_response(context)

class AcrilCatalog(ListView):
    template_name = 'fronttemp/acril_catalog.html'
    context_object_name = 'stones'
    ordering = ['name_stone']
    paginate_by = None \

    def get_queryset(self):
        queryset = AcrylicStone.objects.filter(archive=False).only(
            'name_stone',
            'priview_img',
            'brand_stone',
            'color',
            'texture',
            'faktura',
        )

        brand = self.request.GET.getlist('brand')
        color = self.request.GET.getlist('color')
        texture = self.request.GET.getlist('texture')
        faktura = self.request.GET.getlist('faktura')

        if brand:
            queryset = queryset.filter(brand_stone__in=brand)
        if color:
            queryset = queryset.filter(color__in=color)
        if texture:
            queryset = queryset.filter(texture__in=texture)
        if faktura:
            queryset = queryset.filter(faktura__in=faktura)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['selected_brands'] = self.request.GET.getlist('brand')
        context['selected_colors'] = self.request.GET.getlist('color')
        context['selected_textures'] = self.request.GET.getlist('texture')
        context['selected_fakturas'] = self.request.GET.getlist('faktura')

        stones_qs = AcrylicStone.objects.filter(archive=False)
        context['brand_options'] = list(
            stones_qs.order_by('brand_stone').values_list('brand_stone', flat=True).distinct()
        )
        context['color_options'] = list(
            stones_qs.order_by('color').values_list('color', flat=True).distinct()
        )
        context['texture_options'] = list(
            stones_qs.order_by('texture').values_list('texture', flat=True).distinct()
        )
        context['faktura_options'] = list(
            stones_qs.order_by('faktura').values_list('faktura', flat=True).distinct()
        )

        return context

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('fronttemp/_stones_grid.html', context, request=request)
            return HttpResponse(html)

        return self.render_to_response(context)