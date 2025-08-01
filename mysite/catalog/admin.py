from django.contrib import admin
from django.utils.html import format_html
from .models import Stone, StoneImage, QuartzStone, AcrylicStone, NaturalStone, CeramicsStone

class StoneImageInline(admin.TabularInline):
    model = StoneImage
    extra = 1
    max_num = 10
    fields = ('image_preview', 'image')
    readonly_fields = ('image_preview',)

    def image_preview(self, instance):
        if instance.image and instance.image.url:
            return format_html(
                '<img src="{}" style="max-height:100px;max-width:200px;object-fit:contain;"/>',
                instance.image.url
            )
        return "Нет изображения"

    image_preview.short_description = "Примеры"

class StoneAdminBase(admin.ModelAdmin):
    list_display = ('name_stone', 'pk', 'article', 'material', 'country', 'archive', 'preview_thumbnail')
    list_filter = ('material', 'country', 'archive')
    search_fields = ('name_stone', 'article', 'about_brand')
    list_editable = ('archive',)
    inlines = [StoneImageInline]
    readonly_fields = ('preview_thumbnail',)
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'name_stone',
                'article',
                'material',
                'country',
                'thickness',
                'abt_prise'
            )
        }),
        ('Описание', {
            'fields': ('about_brand',)
        }),
        ('Изображения', {
            'fields': ('priview_img', 'preview_thumbnail'),
        }),
        ('Статус', {
            'fields': ('archive',),
            'classes': ('collapse',)
        }),
    )

    def preview_thumbnail(self, obj):
        if obj.priview_img and obj.priview_img.url:
            return format_html(
                '<img src="{}" style="max-height:200px;max-width:300px;object-fit:contain;"/>',
                obj.priview_img.url
            )
        return "Нет превью"

    preview_thumbnail.short_description = 'Предпросмотр'

@admin.register(QuartzStone)
class QuartzStoneAdmin(StoneAdminBase):
    fieldsets = StoneAdminBase.fieldsets + (
        ('Характеристики кварца', {
            'fields': (
                'brand_stone',
                'color',
                'texture',
                'faktura',
                'link_serf'
            )
        }),
    )

@admin.register(AcrylicStone)
class AcrylicStoneAdmin(StoneAdminBase):
    fieldsets = StoneAdminBase.fieldsets + (
        ('Характеристики акрила', {
            'fields': (
                'brand_stone',
                'color',
                'texture',
                'faktura',
                'link_serf'
            )
        }),
    )

@admin.register(NaturalStone)
class NaturalStoneAdmin(StoneAdminBase):
    fieldsets = StoneAdminBase.fieldsets + (
        ('Характеристики природного камня', {
            'fields': (
                'brand_stone',
                'color',
                'texture',
                'faktura',
                'link_serf'
            )
        }),
    )

@admin.register(CeramicsStone)
class CeramicsStoneAdmin(StoneAdminBase):
    fieldsets = StoneAdminBase.fieldsets + (
        ('Характеристики керамики', {
            'fields': (
                'brand_stone',
                'color',
                'texture',
                'faktura',
                'link_serf'
            )
        }),
    )

@admin.register(StoneImage)
class StoneImageAdmin(admin.ModelAdmin):
    list_display = ('stone_info', 'image_preview')
    search_fields = ('stone__name_stone', 'stone__article')
    list_filter = ('stone__material',)
    readonly_fields = ('image_preview',)
    fields = ('stone', 'image', 'image_preview')

    def stone_info(self, obj):
        return f"{obj.stone.name_stone} (арт. {obj.stone.article})"

    stone_info.short_description = 'Камень'

    def image_preview(self, obj):
        if obj.image and obj.image.url:
            return format_html(
                '<img src="{}" style="max-height:300px;max-width:400px;object-fit:contain;"/>',
                obj.image.url
            )
        return "Нет изображения"

    image_preview.short_description = 'Примеры'