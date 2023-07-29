import time
from datetime import datetime
from telegram_bot import send_telegram_message
from flask import jsonify

def daily_report(flask_app, app):
    @flask_app.route('/daily_update', methods=['GET'])
    def daily():
        current_time_millis = int(time.time() * 1000)
        start_time_millis = current_time_millis - (24 * 60 * 60 * 1000)
        daily_pnl = 0
        trades = app.client.get_account_trades(symbol="BTCUSDT", startTime=start_time_millis, endTime=current_time_millis, recvWindow=10000)
        for trade in trades:
            daily_pnl += float(trade['realizedPnl'])
        # Get the current portfolio value
        account = app.client.account()
        portfolio_value_now = float(account['totalWalletBalance'])

        portfolio_value_yesterday = portfolio_value_now - daily_pnl
        daily_pnl_percent = round((daily_pnl/portfolio_value_now)*100, 2)

        # Send the report
        response = send_report(round(portfolio_value_now, 1), round(daily_pnl,1), daily_pnl_percent, round(portfolio_value_yesterday,1))

        return jsonify(response), 200
    
    return daily

def send_report(portfolio_value, daily_pnl, daily_pnl_percent, portfolio_value_yesterday):
    report_date = datetime.now().strftime("%d/%m/%Y")

    report = '\n'.join([
        f"Daily report {report_date}:",
        f"Portfolio value: {portfolio_value}",
        f"Starting balance: {portfolio_value_yesterday}",
        f"Daily P&L: {daily_pnl}$",
        f"Daily P&L percent: {daily_pnl_percent}%"
    ]) 
    send_telegram_message(report)
    return report
        