from yookassa import Configuration, Payment
import uuid
from django.conf import settings

Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


def create_payment(order, return_url):
    base_url = settings.WEBHOOK_URL
    if not base_url or not base_url.startswith('http'):
        raise ValueError("WEBHOOK_URL должен быть указан в настройках и начинаться с http или https")
    
    return_url = f"{base_url.rstrip('/')}{return_url}?orderId={order.id}" if return_url.startswith('/') else return_url

    payment = Payment.create({
        "amount": {
            "value": str(order.amount),
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": return_url
        },
        "capture": True,
        "description": f"Оплата заказа №{order.id}",
        "metadata": {
            "order_id": str(order.id)
        }
    }, str(uuid.uuid4()))

    return payment