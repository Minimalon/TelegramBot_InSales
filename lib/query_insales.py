import json
import re

from insales import InSalesApi
from lib import query_db
import config

api = InSalesApi.from_credentials(config.account_name, config.api_key, config.api_pass)


def get_product(product_id):
    return api.get_product(product_id)


def create_order(chat_id):
    order_info = query_db.get_order_info(chat_id=chat_id)
    order = api.create_order({
        'client': {
            'phone': order_info.client_phone,
            'name': order_info.client_name,
            'consent_to_personal_data': 'true',
            'subscribe': 'true',
            'messenger-subscription': 'true',
        },
        'order-lines-attributes': [{
            'product-id': order_info.product_id,
            'quantity': order_info.quantity,
        }],
        "currency-code": order_info.currency,
        'payment-gateway-id': order_info.paymentGateway,
        'delivery-variant-id': 5563162,
    })
    json.dump(order, open('json/order.json', 'w'), indent=4, sort_keys=True, default=str)
    query_db.create_historyOrder(order_id=order['id'], chat_id=order_info.chat_id, first_name=order_info.first_name,
                                 paymentGateway=order_info.paymentGateway, product_id=order_info.product_id,
                                 price=order_info.price, quantity=order_info.quantity, currency=order_info.currency,
                                 client_name=order_info.client_name, client_phone=order_info.client_phone,
                                 client_mail=order_info.client_mail)
    return order


def get_name_paymentGateway(id):
    for payment in api.get_payment_gateways():
        if payment['id'] == int(id):
            return payment['title']


def get_paymentGateway(id):
    for payment in api.get_payment_gateways():
        if payment['id'] == int(id):
            return payment


def convert_price(chat_id, price):
    currency = query_db.get_order_info(chat_id=chat_id).currency
    if currency == "RUR":
        return price
    if currency == "USD":
        for cur in api.get_stock_currencies():
            if cur['code'] == 'USD':
                return round(float(price) / cur['cb-rate'], 0)


def convert_price_to_RUR(chat_id, price):
    currency = query_db.get_order_info(chat_id=chat_id).currency
    if currency == "RUR":
        return price
    if currency == "USD":
        for cur in api.get_stock_currencies():
            if cur['code'] == 'USD':
                return round(float(price) * cur['cb-rate'], 0)


def update_price_on_product(product_id, price):
    for i in api.get_product_variants(product_id):
        api.update_product_variant(i['product-id'], i['id'], {'price': float(price)})


def get_photos(product_id):
    return [i['medium-url'] for i in api.get_product_images(product_id)]


if __name__ == '__main__':
    print(api.get_application_widgets())
