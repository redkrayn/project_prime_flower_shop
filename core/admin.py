from django.contrib import admin
from .models import Bouquet, Customer, Courier, Order, Consultation


@admin.register(Bouquet)
class BouquetAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'occasion', 'budget')  
    search_fields = ('name', 'description')  
    list_filter = ('occasion', 'budget')  

admin.site.register(Customer)
admin.site.register(Courier)
admin.site.register(Order)
admin.site.register(Consultation)