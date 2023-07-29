import os
from flask import Flask
from binance.um_futures import UMFutures
from order_module import process_alert
from daily_update_module import daily_report
from open_order import open_order


class BinanceApp:
    def __init__(self, api_key, api_secret):
        self.client = UMFutures(key=api_key, secret=api_secret)
        self.positions = self.client.account()

api_key = os.environ['API_KEY']
api_secret = os.environ['API_SECRET']
app = BinanceApp(api_key, api_secret)

flask_app = Flask(__name__)

process_alert(flask_app, app)
daily_report(flask_app, app)
open_order(flask_app, app)

