from django.contrib import admin
from django.utils.html import format_html
from .models import Bouquet, Customer, Courier, Order, Consultation

@admin.register(Bouquet)
class BouquetAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'occasion', 'budget', 'image_preview')
    search_fields = ('name', 'description', 'composition')
    list_filter = ('occasion', 'budget')
    list_per_page = 10  
    ordering = ('id',)  
    fieldsets = (
        (None, {
            'fields': ('name', 'price', 'image', 'image_preview'),
            'description': 'Основные данные букета'
        }),
        ('Подробности', {
            'fields': ('description', 'composition'),
            'description': 'Описание и состав букета'
        }),
        ('Категоризация', {
            'fields': ('occasion', 'budget'),
            'description': 'Повод и бюджет для фильтрации'
        }),
    )
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px; object-fit: cover; border-radius: 4px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);" />', obj.image.url)
        return "Нет изображения"
    image_preview.short_description = 'Превью'

admin.site.register(Customer)
admin.site.register(Courier)
admin.site.register(Order)
admin.site.register(Consultation)