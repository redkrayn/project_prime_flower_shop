from django import forms
from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html
from django.http import HttpResponse
from django.db.models import Count

from .models import Bouquet, Customer, Courier, Order, Consultation, Florist

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

                field_obj = meta.get_field(field)
                if field_obj.choices:
                    value = getattr(obj, f'get_{field}_display')()

                if callable(value):
                    value = value()
                row.append(str(value) if value is not None else '')
            writer.writerow(row)

        return response


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin, ExportCsvMixin):
    change_list_template = "change_list.html"
    list_display = ('id', 'customer', 'bouquet', 'courier', 'status', 'payment_status', 'amount', 'created_at', 'delivery_time')
    list_filter = ('status', 'payment_status', 'courier', 'created_at')
    search_fields = ('customer__name', 'bouquet__name', 'delivery_address')
    list_editable = ('courier', 'status', 'payment_status')
    list_per_page = 25
    date_hierarchy = 'created_at'
    actions = ['export_as_csv', 'mark_as_delivered', 'mark_as_paid', 'assign_courier']
    fieldsets = (
        (None, {'fields': ('customer', 'bouquet', 'courier')}),
        ('Детали доставки', {'fields': ('delivery_address', 'delivery_time')}),
        ('Статус', {'fields': ('status', 'payment_status', 'amount', 'yookassa_payment_id')}),
    )

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

    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')
    mark_as_delivered.short_description = 'Отметить как доставлено'

    def mark_as_paid(self, request, queryset):
        queryset.update(payment_status='paid')
    mark_as_paid.short_description = 'Отметить как оплачено'

    def assign_courier(self, request, queryset):
        active_courier = Courier.objects.filter(is_active=True).first()
        if active_courier:
            queryset.update(courier=active_courier)
            self.message_user(request, f"Назначен курьер: {active_courier.name}")
        else:
            self.message_user(request, "Нет активных курьеров", level='error')
    assign_courier.short_description = 'Назначить активного курьера'


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number')
    search_fields = ('name', 'phone_number')
    list_per_page = 20


@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'tg_chat_id', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'phone_number')
    list_editable = ('is_active',)
    list_per_page = 20


@admin.register(Florist)
class FloristAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'tg_chat_id', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'phone_number')
    list_editable = ('is_active',)
    list_per_page = 20


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'florist', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer__name', 'florist__name')
    list_editable = ('status', 'florist')
    list_per_page = 20
    date_hierarchy = 'created_at'
