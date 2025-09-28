import requests
from django.conf import settings
from django.db.models import Count

from core.models import Bouquet, Courier, Florist
from project_prime_flower_shop.settings import TELEGRAM_DEFAULT_CHAT_ID


def get_employee_chat_id(role):
    if role == 'florist':
        florist = Florist.objects.filter(is_active=True).annotate(
            num_consultations=Count('consultation')
        ).order_by('num_consultations').first()
        return florist.tg_chat_id if florist else None

    elif role == 'courier':
        courier = Courier.objects.filter(is_active=True).annotate(
            num_orders=Count('order')
        ).order_by('num_orders').first()
        return courier.tg_chat_id if courier else None


def send_msg_to_florist(consultation, quiz_results=None):
    created_at_str = consultation.created_at.strftime("%d.%m.%Y %H:%M")

    telegram_message = (
        f"🌸 Новая заявка на консультацию для флориста!\n"
        f"👤 Имя клиента: {consultation.customer.name}\n"
        f"📞 Телефон: {consultation.customer.phone_number}\n"
        f"📅 Дата обращения: {created_at_str}\n"
        f"🆔 ID консультации: {consultation.id}\n"
    )

    if quiz_results:
        ru_occasion = dict(Bouquet.OCCASIONS).get(quiz_results.get('occasion'), '—')
        ru_budget = dict(Bouquet.BUDGETS).get(quiz_results.get('budget'), '—')
        telegram_message += (
            f"🎁 Повод для покупки: {ru_occasion}\n"
            f"💰 Бюджет: {ru_budget}\n"
        )

    chat_id = get_employee_chat_id('florist')

    if chat_id:
        florist = Florist.objects.filter(tg_chat_id=chat_id).first()
        if florist:
            consultation.florist = florist
            consultation.save()
    else:
        chat_id = TELEGRAM_DEFAULT_CHAT_ID
        telegram_message += (
            "⚠️ Не удалось назначить флориста для консультации, "
            "укажите сотрудника в админ-панели\n"
        )

    telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    telegram_data = {
        'chat_id': chat_id,
        'text': telegram_message
    }
    requests.post(telegram_url, data=telegram_data)


def send_msg_to_courier(order):
    created_at_str = order.created_at.strftime("%d.%m.%Y %H:%M")

    telegram_message = (
        f"🚚 Новый заказ для курьера!\n"
        f"👤 Имя клиента: {order.customer.name}\n"
        f"🆔 Идентификатор заказа: {order.id}\n"
        f"📞 Телефон: {order.customer.phone_number}\n"
        f"📅 Дата оформления: {created_at_str}\n"
        f"💰 Сумма заказа: {order.amount}\n"
    )

    chat_id = get_employee_chat_id('courier')

    if chat_id:
        courier = Courier.objects.filter(tg_chat_id=chat_id).first()
        if courier:
            order.courier = courier
            order.save()
    else:
        chat_id = TELEGRAM_DEFAULT_CHAT_ID
        telegram_message += (
            "⚠️ Не удалось назначить курьера для доставки, "
            "укажите сотрудника в админ-панели\n"
        )

    telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    telegram_data = {
        'chat_id': chat_id,
        'text': telegram_message
    }
    requests.post(telegram_url, data=telegram_data)
