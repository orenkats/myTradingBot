from telegram_bot import send_telegram_message

def open_order(flask_app, app):
    @flask_app.route('/open_order', methods=['GET'])
    def print_order():
        account = app.client.account()
        if(float(account['totalWalletBalance']) == float(account['availableBalance'])):
            print("No open trades")
            return "No open trades"
        
        ticker_price_dict = app.client.ticker_price("BTCUSDT")
        current_price = float(ticker_price_dict['price'])
        unfilled_orders = app.client.get_orders(symbol="BTCUSDT", recvWindow=10000)
        if(unfilled_orders):
            limit_price = round(float(unfilled_orders[0]['price']),1)
            open_order_msg =  '\n'.join([
            f"Open order details:",
            f"Not activated",
            f"Limit price: {limit_price}",
            f"Current price: {round(current_price,1)}",
        ])
            send_telegram_message(open_order_msg)
        for position in account['positions']:
            if position['symbol'] == 'BTCUSDT':  
                entry_price = float(position['entryPrice'])
                if entry_price == 0: 
                    print("No position")
                    return "No position"
                current_pnl = float(position['unrealizedProfit'])
                break
        total_wallet_balance = float(account['totalWalletBalance'])
        current_pnl_percent = round((current_pnl/total_wallet_balance)*100,2)

        msg = '\n'.join([
            f"Live position details:",
            f"Entry price: {round(entry_price,1)}",
            f"Current price: {round(current_price,1)}",
            f"Current P&L: {round(current_pnl,1)}$",
            f"Current P&L percent: {current_pnl_percent}%"
        ])

        send_telegram_message(msg)

        print("Success")
        return "Success"
    return print_order
