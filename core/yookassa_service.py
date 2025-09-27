from yookassa import Configuration, Payment
import uuid
from django.conf import settings

Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


def create_payment(order, return_url):
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
            "order_id": order.id
        }
    }, str(uuid.uuid4()))

    return payment