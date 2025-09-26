import requests
from django.conf import settings

from core.models import Bouquet


def send_msg_to_florist(first_name, phone_number, consultation, quiz_results=None):
    telegram_message = (
            f"Новая заявка на консультацию для флориста!\n"
            f"Имя: {first_name}\n"
            f"Телефон: {phone_number}\n"
            f"Дата: {consultation}"
        )

    if quiz_results:
        ru_occasion = dict(Bouquet.OCCASIONS).get(quiz_results['occasion'])
        ru_budget = dict(Bouquet.BUDGETS).get(quiz_results['budget'])
        telegram_message += (
            f"\nПовод для покупки: {ru_occasion}\n"
            f"Бюджет: {ru_budget}"
        )

    telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    telegram_data = {
        'chat_id': settings.TELEGRAM_CHAT_ID,
        'text': telegram_message
    }
    requests.post(telegram_url, data=telegram_data)


def send_msg_to_courier(name_courier, first_name, phone_number, date):
    telegram_message = (
            f"Вам поступил новый заказ!{name_courier}\n"
            f"От: {first_name}\n"
            f"Телефон: {phone_number}\n"
            f"Дата: {date}"
        )
    telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    telegram_data = {
        'chat_id': settings.TELEGRAM_CHAT_ID,
        'text': telegram_message
    }
    requests.post(telegram_url, data=telegram_data)
