import requests
from django.conf import settings


def send_msg_to_florist(first_name, phone_number, consultation):
    telegram_message = (
            f"Новая заявка на консультацию для флориста!\n"
            f"Имя: {first_name}\n"
            f"Телефон: {phone_number}\n"
            f"Дата: {consultation}"
        )
    telegram_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    telegram_data = {
        'chat_id': settings.TELEGRAM_CHAT_ID,
        'text': telegram_message
    }
    requests.post(telegram_url, data=telegram_data)
