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

    base_message = (
        f"🌸 Новая заявка на консультацию для флориста!\n"
        f"👤 Имя клиента: {consultation.customer.name}\n"
        f"📞 Телефон: {consultation.customer.phone_number}\n"
        f"📅 Дата обращения: {created_at_str}\n"
        f"🆔 ID консультации: {consultation.id}\n"
    )

    if quiz_results:
        ru_occasion = dict(Bouquet.OCCASIONS).get(quiz_results.get('occasion'), '—')
        ru_budget = dict(Bouquet.BUDGETS).get(quiz_results.get('budget'), '—')
        base_message += (
            f"🎁 Повод для покупки: {ru_occasion}\n"
            f"💰 Бюджет: {ru_budget}\n"
        )

    florist = None
    chat_id = get_employee_chat_id("florist")
    if chat_id:
        florist = Florist.objects.filter(tg_chat_id=chat_id).first()

    telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    if florist:
        response = requests.post(
            telegram_url,
            data={"chat_id": florist.tg_chat_id, "text": base_message}
        )

        if response.status_code == 200 and response.json().get("ok", False):
            consultation.florist = florist
            consultation.save()
        else:
            send_fallback_message(base_message, "Ошибка при отправке сообщения флористу")
    else:
        send_fallback_message(base_message, "Флорист не найден")


def send_msg_to_courier(order):
    created_at_str = order.created_at.strftime("%d.%m.%Y %H:%M")

    base_message = (
        f"🚚 Новый заказ для курьера!\n"
        f"👤 Имя клиента: {order.customer.name}\n"
        f"🆔 Идентификатор заказа: {order.id}\n"
        f"📞 Телефон: {order.customer.phone_number}\n"
        f"📅 Дата оформления: {created_at_str}\n"
        f"💰 Сумма заказа: {order.amount}\n"
    )

    courier = None
    chat_id = get_employee_chat_id("courier")
    if chat_id:
        courier = Courier.objects.filter(tg_chat_id=chat_id).first()

    telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"

    if courier:
        response = requests.post(
            telegram_url,
            data={"chat_id": courier.tg_chat_id, "text": base_message}
        )

        if response.status_code == 200 and response.json().get("ok", False):
            order.courier = courier
            order.save()
        else:
            send_fallback_message(base_message, "Ошибка при отправке сообщения курьеру")
    else:
        send_fallback_message(base_message, "Курьер не найден")


def send_fallback_message(base_message, reason):
    message = (
        base_message
        + "\n⚠️ " + reason
        + "\nВыберите сотрудника в админ-панели."
    )

    telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(
        telegram_url,
        data={"chat_id": TELEGRAM_DEFAULT_CHAT_ID, "text": message}
    )
