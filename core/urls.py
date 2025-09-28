from django.urls import path
from .views import (
    index, quiz, quiz_step, result, catalog, consultation,
    order, bouquet_detail, yookassa_webhook, payment_failed,
    payment_success, load_more_bouquets, privacy_policy
)


urlpatterns = [
    path('', index, name='index'),
    path('quiz/', quiz, name='quiz'),
    path('quiz-step/', quiz_step, name='quiz_step'),
    path('result/', result, name='result'),
    path('catalog/', catalog, name='catalog'),
    path('bouquet/<int:bouquet_id>/', bouquet_detail, name='bouquet_detail'),
    path('consultation/', consultation, name='consultation'),
    path('order/', order, name='order'),
    path('payment/success/', payment_success, name='payment_success'),
    path('payment/failed/', payment_failed, name='payment_failed'),
    path('yookassa-webhook/', yookassa_webhook, name='yookassa_webhook'),
    path('load-more-bouquets/', load_more_bouquets, name='load_more_bouquets'),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
]