from django.urls import path
from .views import index, quiz, quiz_step, result, catalog, consultation, order, order_step, bouquet_detail


urlpatterns = [
    path('', index, name='index'),
    path('quiz/', quiz, name='quiz'),
    path('quiz-step/', quiz_step, name='quiz_step'),
    path('result/', result, name='result'),
    path('catalog/', catalog, name='catalog'),
    path('bouquet/<int:bouquet_id>/', bouquet_detail, name='bouquet_detail'),
    path('consultation/', consultation, name='consultation'),
    path('order/', order, name='order'),
    path('order-step/', order_step, name='order_step'),
]