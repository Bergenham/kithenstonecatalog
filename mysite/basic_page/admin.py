from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import InfoStone, StoneDescription, Company

class StoneDescriptionInline(admin.StackedInline):
    model = StoneDescription
    extra = 1
    fields = ('name', 'full_description', 'image_description')
    show_change_link = True

class CompanyInline(admin.TabularInline):
    model = Company.produced_stones.through
    extra = 1
    verbose_name = "Производитель"
    verbose_name_plural = "Производители"
    autocomplete_fields = ['company']

@admin.register(InfoStone)
class InfoStoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'another_name', 'main_image_preview', 'companies_links')
    search_fields = ('name', 'another_name')
    list_filter = ('manufacturers',)
    inlines = [StoneDescriptionInline, CompanyInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'another_name', 'main_image')
        }),
        ('Связанные объекты', {
            'fields': ('companies_links',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('companies_links',)

    @admin.display(description="Главное изображение")
    def main_image_preview(self, obj):
        return format_html('<img src="{}" height="50" />', obj.main_image.url) if obj.main_image else "-"

    def companies_links(self, obj):
        companies = obj.manufacturers.all()
        return format_html("<br>".join(
            f'<a href="{reverse("admin:basic_page_company_change", args=(c.id,))}">{c.name}</a>' for c in companies
        )) if companies else "-"
    companies_links.short_description = "Производители"

@admin.register(StoneDescription)
class StoneDescriptionAdmin(admin.ModelAdmin):
    list_display = ('info_stone_link', 'name', 'full_description', 'image_preview')
    list_select_related = ('info_stone',)
    readonly_fields = ('info_stone_link',)
    fieldsets = (
        (None, {
            'fields': ('info_stone_link', 'name', 'full_description')
        }),
        ('Медиа', {
            'fields': ('image_description', 'image_preview'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description="Камень")
    def info_stone_link(self, obj):
        url = reverse('admin:basic_page_infostone_change', args=(obj.info_stone.id,))
        return format_html('<a href="{}">{}</a>', url, obj.info_stone.name)

    @admin.display(description="Превью")
    def image_preview(self, obj):
        return format_html('<img src="{}" height="50" />', obj.image_description.url) if obj.image_description else "-"

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_image_preview', 'produced_stones_list')
    search_fields = ('name',)
    filter_horizontal = ('produced_stones',)
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Медиа', {
            'fields': ('company_image', 'company_image_preview'),
            'classes': ('collapse',)
        }),
        ('Производство', {
            'fields': ('produced_stones',),
            'classes': ('wide',)
        }),
    )
    readonly_fields = ('company_image_preview',)

    @admin.display(description="Превью логотипа")
    def company_image_preview(self, obj):
        return format_html('<img src="{}" height="50" />', obj.company_image.url) if obj.company_image else "-"

    @admin.display(description="Производимые камни")
    def produced_stones_list(self, obj):
        stones = obj.produced_stones.all()
        return format_html("<br>".join(
            f'<a href="{reverse("admin:basic_page_infostone_change", args=(s.id,))}">{s.name}</a>' for s in stones
        )) if stones else "-"

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('produced_stones')