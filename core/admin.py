from django.contrib import admin
from .models import Bouquet, Customer, Courier, Order, Consultation


admin.site.register(Bouquet)
admin.site.register(Customer)
admin.site.register(Courier)
admin.site.register(Order)
admin.site.register(Consultation)