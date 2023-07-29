import requests, os


def send_telegram_message(text):
    bot_token = os.environ['TelegramBotToken'] 
    chat_id = os.environ['TelegramChatId'] 

    max_chars = 4096
    for i in range(0, len(text), max_chars):
        chunk = text[i:i+max_chars]
        send_message_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(send_message_url, data={"chat_id": chat_id, "text": chunk})
