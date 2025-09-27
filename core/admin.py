from django import forms
from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html
from django.http import HttpResponse
from django.db.models import Count

from .models import Bouquet, Customer, Courier, Order, Consultation

import codecs
import csv


class BouquetForm(forms.ModelForm):
    class Meta:
        model = Bouquet
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5, 'cols': 50}),
            'composition': forms.Textarea(attrs={'rows': 5, 'cols': 50}),
        }


@admin.register(Bouquet)
class BouquetAdmin(admin.ModelAdmin):
    form = BouquetForm
    list_display = (
        'id',
        'name',
        'price',
        'occasion',
        'budget',
        'image_preview',
        'created_orders_count',
    )
    search_fields = ('name', 'description', 'composition')
    list_filter = ('occasion', 'budget')
    list_editable = ('price', 'occasion', 'budget')
    list_per_page = 25
    ordering = ('id',)
    fieldsets = (
        (None, {
            'fields': ('name', 'price', 'image', 'image_preview'),
            'description': 'Основные данные букета',
        }),
        ('Подробности', {
            'fields': ('description', 'composition'),
            'description': 'Описание и состав букета',
        }),
        ('Категоризация', {
            'fields': ('occasion', 'budget'),
            'description': 'Повод и бюджет для фильтрации',
        }),
    )
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; '
                'object-fit: cover; border-radius: 4px; '
                'box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);" />',
                obj.image.url,
            )
        return "Нет изображения"

    image_preview.short_description = 'Превью'

    def created_orders_count(self, obj):
        return obj.orders.count()

    created_orders_count.short_description = 'Кол-во заказов'


class ExportCsvMixin:
    """Сделано не по документации, а по гайду какого-то чела с юпуба"""

    def export_as_csv(self, request, queryset):
        meta = self.model._meta

        field_verbose_names = [field.verbose_name for field in meta.fields]
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = (
            f'attachment; filename={meta.verbose_name_plural}.csv'
        )
        response.write(codecs.BOM_UTF8.decode('utf-8'))

        writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_ALL)

        writer.writerow(field_verbose_names)

        for obj in queryset:
            row = []
            for field in field_names:
                value = getattr(obj, field)
                if callable(value):
                    value = value()
                row.append(str(value) if value is not None else '')
            writer.writerow(row)

        return response


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin, ExportCsvMixin):
    change_list_template = "change_list.html"
    actions = ["export_as_csv"]
    list_display = ['get_customer_phone', 'bouquet', 'amount', 'payment_status', 'created_at']
    list_filter = ['payment_status', 'created_at']

    def changelist_view(self, request, extra_context=None):
        queryset = self.get_queryset(request)

        payment_filter_applied = any(
            key.startswith('payment_status') for key in request.GET.keys()
        )

        total_amount = None
        if not payment_filter_applied:
            total_amount = queryset.aggregate(total=Sum('amount'))['total'] or 0

        statuses = ['paid', 'pending', 'failed']
        totals = {}

        current_status = request.GET.get('payment_status__exact')

        if current_status in statuses:
            totals[current_status] = queryset.filter(payment_status=current_status).aggregate(
                total=Sum('amount')
            )['total'] or 0

        top_customers = self.get_top_customers()
        top_bouquets = self.get_top_bouquets()

        if extra_context is None:
            extra_context = {}

        extra_context['total_amount'] = total_amount
        extra_context['totals'] = totals
        extra_context['current_status'] = current_status
        extra_context['top_customers'] = top_customers
        extra_context['top_bouquets'] = top_bouquets

        return super().changelist_view(request, extra_context=extra_context)

    @staticmethod
    def get_top_customers():
        top_customers_data = Order.objects.values(
            'customer__phone_number'
        ).annotate(
            order_count=Count('id')
        ).order_by('-order_count')[:3]

        top_customers = []
        for customer in top_customers_data:
            top_customers.append({
                'phone_number': customer['customer__phone_number'],
                'order_count': customer['order_count']
            })
        return top_customers

    @staticmethod
    def get_top_bouquets():
        top_bouquets_data = Order.objects.values(
            'bouquet__name'
        ).annotate(
            order_count=Count('id')
        ).order_by('-order_count')[:3]

        top_bouquets = []
        for bouquet in top_bouquets_data:
            top_bouquets.append({
                'name': bouquet['bouquet__name'],
                'order_count': bouquet['order_count']
            })
        return top_bouquets

    def get_customer_phone(self, obj):
        return obj.customer.phone_number

    get_customer_phone.short_description = 'Телефон покупателя'
    get_customer_phone.admin_order_field = 'customer__phone_number'


admin.site.register(Customer)
admin.site.register(Courier)
admin.site.register(Consultation)
