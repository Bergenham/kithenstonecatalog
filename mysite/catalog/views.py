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

def stone_detail_q(request, article_get=None):
    if article_get:
        stone = get_object_or_404(QuartzStone.objects.filter(archive=False), article=article_get)
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

    return render(request, 'fronttemp/quartz/about_quartz.html', {
        'stone': stone,
        'img_m': images,
    })

def stone_detail_c(request, article_get=None):
    if article_get:
        stone = get_object_or_404(CeramicsStone.objects.filter(archive=False), article=article_get)
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

    return render(request, 'fronttemp/ceramic/about_ceramic.html', {
        'stone': stone,
        'img_m': images,
    })

def stone_detail_a(request, article_get=None):
    if article_get:
        stone = get_object_or_404(AcrylicStone.objects.filter(archive=False), article=article_get)
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

    return render(request, 'fronttemp/acril/about_acril.html', {
        'stone': stone,
        'img_m': images,
    })

def stone_detail_n(request, article_get=None):
    if article_get:
        stone = get_object_or_404(NaturalStone.objects.filter(archive=False), article=article_get)
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

    return render(request, 'fronttemp/natural/about_natural.html', {
        'stone': stone,
        'img_m': images,
    })

class QuartzCatalog(ListView):
    template_name = 'fronttemp/quartz/quartz_catalog.html'
    context_object_name = 'stones'
    ordering = ['name_stone']
    paginate_by = None

    PAGE_SIZE = 20  # количество элементов на страницу

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
        """
        Возвращаем и выбранные фильтры, и варианты (brand_options и т.д.),
        и сами камни (sliced_qs), и счётчики для кнопки load more.
        """
        context = super().get_context_data(**kwargs)

        # выбранные фильтры
        context['selected_brands'] = self.request.GET.getlist('brand')
        context['selected_colors'] = self.request.GET.getlist('color')
        context['selected_textures'] = self.request.GET.getlist('texture')
        context['selected_fakturas'] = self.request.GET.getlist('faktura')

        # ВСЕ варианты для фильтров (берём из всех камней, не только отфильтрованных!)
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
        full_qs = self.get_queryset()
        total_count = full_qs.count()

        try:
            offset = int(request.GET.get('offset', 0))
            if offset < 0:
                offset = 0
        except (ValueError, TypeError):
            offset = 0

        sliced_qs = full_qs[offset: offset + self.PAGE_SIZE]

        # ВАЖНО: назначаем self.object_list для работы ListView
        self.object_list = sliced_qs

        context = self.get_context_data()
        context['stones'] = sliced_qs
        context['total_count'] = total_count
        context['offset'] = offset
        context['page_size'] = self.PAGE_SIZE

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('fronttemp/quartz/_stones_grid_Q.html ', context, request=request)
            return JsonResponse({'html': html, 'total': total_count, 'offset': offset})

        return self.render_to_response(context)


class CeramicCatalog(ListView):
    template_name = 'fronttemp/ceramic/ceramic_catalog.html'
    context_object_name = 'stones'
    ordering = ['name_stone']
    paginate_by = None

    PAGE_SIZE = 20  # количество элементов на страницу

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
        """
        Возвращаем и выбранные фильтры, и варианты (brand_options и т.д.),
        и сами камни (sliced_qs), и счётчики для кнопки load more.
        """
        context = super().get_context_data(**kwargs)

        # выбранные фильтры
        context['selected_brands'] = self.request.GET.getlist('brand')
        context['selected_colors'] = self.request.GET.getlist('color')
        context['selected_textures'] = self.request.GET.getlist('texture')
        context['selected_fakturas'] = self.request.GET.getlist('faktura')

        # ВСЕ варианты для фильтров (берём из всех камней, не только отфильтрованных!)
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
        full_qs = self.get_queryset()
        total_count = full_qs.count()

        try:
            offset = int(request.GET.get('offset', 0))
            if offset < 0:
                offset = 0
        except (ValueError, TypeError):
            offset = 0

        sliced_qs = full_qs[offset: offset + self.PAGE_SIZE]

        # ВАЖНО: назначаем self.object_list для работы ListView
        self.object_list = sliced_qs

        context = self.get_context_data()
        context['stones'] = sliced_qs
        context['total_count'] = total_count
        context['offset'] = offset
        context['page_size'] = self.PAGE_SIZE

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('fronttemp/ceramic/_stones_grid_C.html', context, request=request)
            return JsonResponse({'html': html, 'total': total_count, 'offset': offset})

        return self.render_to_response(context)

class NaturalCatalog(ListView):
    template_name = 'fronttemp/natural/natural_catalog.html'
    context_object_name = 'stones'
    ordering = ['name_stone']
    paginate_by = None

    PAGE_SIZE = 20  # количество элементов на страницу

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
        """
        Возвращаем и выбранные фильтры, и варианты (brand_options и т.д.),
        и сами камни (sliced_qs), и счётчики для кнопки load more.
        """
        context = super().get_context_data(**kwargs)

        # выбранные фильтры
        context['selected_brands'] = self.request.GET.getlist('brand')
        context['selected_colors'] = self.request.GET.getlist('color')
        context['selected_textures'] = self.request.GET.getlist('texture')
        context['selected_fakturas'] = self.request.GET.getlist('faktura')

        # ВСЕ варианты для фильтров (берём из всех камней, не только отфильтрованных!)
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
        full_qs = self.get_queryset()
        total_count = full_qs.count()

        try:
            offset = int(request.GET.get('offset', 0))
            if offset < 0:
                offset = 0
        except (ValueError, TypeError):
            offset = 0

        sliced_qs = full_qs[offset: offset + self.PAGE_SIZE]

        # ВАЖНО: назначаем self.object_list для работы ListView
        self.object_list = sliced_qs

        context = self.get_context_data()
        context['stones'] = sliced_qs
        context['total_count'] = total_count
        context['offset'] = offset
        context['page_size'] = self.PAGE_SIZE

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('fronttemp/natural/_stones_grid_N.html', context, request=request)
            return JsonResponse({'html': html, 'total': total_count, 'offset': offset})

        return self.render_to_response(context)

class AcrilCatalog(ListView):
    template_name = 'fronttemp/acril/acril_catalog.html'
    context_object_name = 'stones'
    ordering = ['name_stone']
    paginate_by = None

    PAGE_SIZE = 20  # количество элементов на страницу

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
        """
        Возвращаем и выбранные фильтры, и варианты (brand_options и т.д.),
        и сами камни (sliced_qs), и счётчики для кнопки load more.
        """
        context = super().get_context_data(**kwargs)

        # выбранные фильтры
        context['selected_brands'] = self.request.GET.getlist('brand')
        context['selected_colors'] = self.request.GET.getlist('color')
        context['selected_textures'] = self.request.GET.getlist('texture')
        context['selected_fakturas'] = self.request.GET.getlist('faktura')

        # ВСЕ варианты для фильтров (берём из всех камней, не только отфильтрованных!)
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
        full_qs = self.get_queryset()
        total_count = full_qs.count()

        try:
            offset = int(request.GET.get('offset', 0))
            if offset < 0:
                offset = 0
        except (ValueError, TypeError):
            offset = 0

        sliced_qs = full_qs[offset: offset + self.PAGE_SIZE]

        # ВАЖНО: назначаем self.object_list для работы ListView
        self.object_list = sliced_qs

        context = self.get_context_data()
        context['stones'] = sliced_qs
        context['total_count'] = total_count
        context['offset'] = offset
        context['page_size'] = self.PAGE_SIZE

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('fronttemp/acril/_stones_grid_A.html', context, request=request)
            return JsonResponse({'html': html, 'total': total_count, 'offset': offset})

        return self.render_to_response(context)