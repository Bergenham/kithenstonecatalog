from django.contrib import admin
from django.utils.html import format_html
from .models import UserBidModel

@admin.register(UserBidModel)
class UserBidAdmin(admin.ModelAdmin):
    list_display = (
        'full_name',
        'formatted_phone',
        'email',
        'is_active',
        'created_at',
        'privacy_agreement'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('full_name', 'phone', 'email')
    list_editable = ('is_active',)
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'privacy_agreement')

    fieldsets = (
        ('Персональные данные', {
            'fields': ('full_name', 'phone', 'email')
        }),
        ('Статус и соглашения', {
            'fields': ('is_active', 'privacy_agreement')
        }),
        ('Системная информация', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def formatted_phone(self, obj):
        return format_html('<span style="font-weight:bold;">{}</span>', obj.phone)
    formatted_phone.short_description = 'Телефон'

    def privacy_agreement(self, obj):
        return '✅' if obj.AWtPP else '❌'
    privacy_agreement.short_description = 'Согласие'

    actions = ['make_inactive']

    @admin.action(description="Деактивировать выбранные заявки")
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} заявок деактивировано")