import requests
import logging

class NotificationSystem:
    def __init__(self, config):
        self.config = config
        self.telegram_bot_token = config.get('telegram_bot_token')
        self.telegram_chat_id = config.get('telegram_chat_id')
        
    def send_telegram_message(self, message):
        if not all([self.telegram_bot_token, self.telegram_chat_id]):
            return
            
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            requests.post(url, json=payload)
        except Exception as e:
            logging.error(f"Telegram notification error: {str(e)}")
            
    def send_trade_notification(self, trade_info):
        message = f"""
🔔 交易提醒
幣對: {trade_info['symbol']}
類型: {trade_info['type']}
價格: {trade_info['price']}
數量: {trade_info['amount']}
時間: {trade_info['timestamp']}
        """
        self.send_telegram_message(message) 