import requests

class TelegramAlert:
    def __init__(self, bot_token, chat_id):
        self.url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self.chat_id = chat_id

    def send(self, message):
        requests.post(self.url, data={
            "chat_id": self.chat_id,
            "text": message
        })
