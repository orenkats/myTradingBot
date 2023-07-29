from flask import request
from binance.error import ClientError
import logging
from telegram_bot import send_telegram_message


def process_alert(flask_app, app):
    @flask_app.route('/', methods=['POST'])
    def process():
        data = request.get_json()
        print("Received data:", data)

        symbol = data['symbol']
        side = (data['side']).upper()
        order_type = (data['type']).upper()
        quantity = data['quantity']
        price = str(round(float(app.client.mark_price("BTCUSDT")['markPrice']),1))
        time_in_force = "GTC"
        type_of_action = data['action'].upper()

        print(f"Extracted information - Symbol: {symbol}, Side: {side}, Order type: {order_type}, Quantity: {quantity}, Price: {price}")

        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity,
            'price': price,
            'timeInForce': time_in_force,
            'typeOfAction': type_of_action
            
        }

        order_response = order(app, params)

        if order_response:
            return {
                "code": "success",
                "message": "order executed"
            }
        else:
            print("order failed")

            return {
                "code": "error",
                "message": "order failed"
            }
    return process


def order(app, params):
    try:
        unfilled_orders = app.client.get_orders(symbol="BTCUSDT", recvWindow=20000)
        if(unfilled_orders):
            response_deleted = app.client.cancel_open_orders(symbol="BTCUSDT", recvWindow=20000)
            print(response_deleted)
            send_telegram_message(response_deleted['msg'])
            if(params['typeOfAction'] == "TP" or params['typeOfAction'] == "SL"):
                return send_telegram_message("Deleted open order, no action has been made")
        if(params['type'] == "MARKET"):
            del params['price']
            del params['timeInForce']
        account = app.client.account()
        pnl = float(account['totalUnrealizedProfit'])
        port_value_before = float(account['totalWalletBalance']) 
        if (port_value_before != float(account['availableBalance'])):
            open_or_close = "Closed"
            if (params['typeOfAction'] == "SL"):
                for position in account['positions']:
                    if position['symbol'] == "BTCUSDT":
                        current_position = position
                        params['quantity'] = str(abs(float(position['positionAmt'])))
                        break
        elif(params['typeOfAction'] == "NEW"):
            open_or_close = "Opened"
        del params['typeOfAction']
        max_attempts = 20
        for attempt in range(max_attempts):
            try:
                response = app.client.new_order(**params)
            # If the order is successful, break the loop
                break
            except ClientError as error:
                logging.error(
                "Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )
                if error.error_code == -2019 and attempt < max_attempts - 1:
                # If the error code is -2019 and we haven't reached the maximum number of attempts, recalculate the position size and try again
                    max_allowed = calculate_position_size(app, port_value_before, attempt)
                    precision = get_market_precision(app)
                    max_allowed = round_to_precision(max_allowed, precision)
                    params['quantity'] = str(max_allowed)
                else:
                    # If the error code is not -2019 or we have reached the maximum number of attempts, send a telegram message and return
                    send_telegram_message('Order failed: {}'.format(error)) # Send a telegram message when order fails
                    return {
                        "code": {error.error_code},
                        "message": "order failed"}

        logging.info(response)

        print("Order parameters:", params)  # Print the order parameters

        fee = round(((float(current_position['entryPrice']) * float(params['quantity']))/100) * 0.04,1)

        if(open_or_close == "Closed"):
            pnl = pnl - fee
            pnl_percent = round((pnl/port_value_before)*100, 2)
            text = '\n'.join([
                f"Trade P&L: {round(pnl,1)}$",
                f"Trade P&L percent: {pnl_percent}%"
            ])
        elif(params['type'] == "LIMIT"):
            text = '\n'.join([
                f"Limit order opened at: {round(float(params['price']), 1)}$",
                f"Fee: {fee}$ "
            ])
        else:
            text = '\n' .join([
                f"Market position opened at: {round(float(current_position['entryPrice']), 1)}$",
                f"Fee: {fee}$ "
            ])


        msg = '\n'.join([
            f"Order executed:",
            f"Symbol: {current_position['symbol']}",
            f"Quantity: {params['quantity']}",
            f"Side: {params['side']}",
            f"Position: {open_or_close}",
            text
        ])
        send_telegram_message(msg)

        return {
            "code": "success",
            "message": "order executed"
        }
    except ClientError as error:
        
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )
        send_telegram_message('Order failed: {}'.format(error)) # Send a telegram message when order fails
        return {
            "code": {error.error_code},
            "message": "order failed"
        }

def calculate_position_size(app, usdt_balance, attempt):
    _leverage=20
    _market="BTCUSDT"

    price = float(app.client.mark_price(_market)['markPrice'])

    qty = (float(usdt_balance) / price) * _leverage
    qty = round(qty * (0.99-(0.01*attempt)) ,8)

    return qty

# get the precision of the market, this is needed to avoid errors when creating orders
def get_market_precision(app, _market="BTCUSDT"):

    market_data = app.client.exchange_info()
    precision = 3
    for market in market_data['symbols']:
        if market['symbol'] == _market:
            precision = market['quantityPrecision']
            break
    return precision

# round the position size we can open to the precision of the market
def round_to_precision(_qty, _precision):
    new_qty = "{:0.0{}f}".format(_qty , _precision)
    return float(new_qty)
