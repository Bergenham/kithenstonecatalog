from django.core.exceptions import ValidationError
from django.views.generic import ListView
from .models import QuartzStone, StoneImage, CeramicsStone, AcrylicStone, NaturalStone
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.http import JsonResponse
from basic_page.models import UserBidModel
from django.http import HttpResponseNotFound

def custom_404_view(request, exception):
    return HttpResponseNotFound(render(request, 'fronttemp/404.html'))

def stone_detail_q(request, stone_id=None):
    if stone_id:
        stone = get_object_or_404(QuartzStone, pk=stone_id)
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
        stone = get_object_or_404(CeramicsStone, pk=stone_id)
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

def stone_detail_a(request, stone_id=None):
    if stone_id:
        stone = get_object_or_404(AcrylicStone, pk=stone_id)
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

def stone_detail_n(request, stone_id=None):
    if stone_id:
        stone = get_object_or_404(NaturalStone, pk=stone_id)
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

class QuartzCatalog(ListView):
    template_name = 'fronttemp/quartz_catalog.html'
    context_object_name = 'stones'
    ordering = ['name_stone']

    def get_queryset(self):
        queryset = QuartzStone.objects.only(
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

        context['brand_choices'] = QuartzStone.BrandStoneChoices.choices
        context['color_choices'] = QuartzStone.ColorChoices.choices
        context['texture_choices'] = QuartzStone.TextureChoices.choices
        context['faktura_choices'] = QuartzStone.FakturaChoices.choices

        return context

class CeramicCatalog(ListView):
    template_name = 'fronttemp/ceramic_catalog.html'
    context_object_name = 'stones'
    ordering = ['name_stone']

    def get_queryset(self):
        queryset = CeramicsStone.objects.only(
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

        context['brand_choices'] = CeramicsStone.BrandStoneChoices.choices
        context['color_choices'] = CeramicsStone.ColorChoices.choices
        context['texture_choices'] = CeramicsStone.TextureChoices.choices
        context['faktura_choices'] = CeramicsStone.FakturaChoices.choices

        return context

class NaturalCatalog(ListView):
    template_name = 'fronttemp/natural_catalog.html'
    context_object_name = 'stones'
    ordering = ['name_stone']

    def get_queryset(self):
        queryset = NaturalStone.objects.only(
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

        context['brand_choices'] = NaturalStone.BrandStoneChoices.choices
        context['color_choices'] = NaturalStone.ColorChoices.choices
        context['texture_choices'] = NaturalStone.TextureChoices.choices
        context['faktura_choices'] = NaturalStone.FakturaChoices.choices

        return context

class AcrilCatalog(ListView):
    template_name = 'fronttemp/acril_catalog.html'
    context_object_name = 'stones'
    ordering = ['name_stone']

    def get_queryset(self):
        queryset = AcrylicStone.objects.only(
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

        context['brand_choices'] = AcrylicStone.BrandStoneChoices.choices
        context['color_choices'] = AcrylicStone.ColorChoices.choices
        context['texture_choices'] = AcrylicStone.TextureChoices.choices
        context['faktura_choices'] = AcrylicStone.FakturaChoices.choices

        return context