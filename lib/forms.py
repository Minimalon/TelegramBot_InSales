#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os.path

from telebot import types
from insales import InSalesApi
from lib import query_db, query_insales
import config
import qrcode

api = InSalesApi.from_credentials(config.account_name, config.api_key, config.api_pass)


def start():
    markup = types.InlineKeyboardMarkup()
    button_order = types.InlineKeyboardButton("Заказ", callback_data='order')
    button_account = types.InlineKeyboardButton("Личный кабинет", callback_data='account')
    button_historyOrders = types.InlineKeyboardButton("История заказов", callback_data='historyOrders')
    markup.row(button_order, button_account)
    markup.row(button_historyOrders)
    text = (f'<u><b>Заказ</b></u> - Оформить заказ покупателю\n\n'
            f'<u><b>Личный кабинет</b></u> - Личные регистрационные данные\n\n'
            f'<u><b>История заказов</b></u> - Список всех раннее оформленных заказов')
    return text, markup


def order():
    markup = types.InlineKeyboardMarkup()
    button_ruble = types.InlineKeyboardButton("₽", callback_data='order-currency_RUR')
    button_dollar = types.InlineKeyboardButton("$", callback_data='order-currency_USD')
    markup.row(button_ruble, button_dollar)
    text = f'Выберите валюту'
    return text, markup


def account(message):
    markup = types.InlineKeyboardMarkup()
    button_main = types.InlineKeyboardButton("Главное меню", callback_data='main')
    markup.row(button_main)
    text = (f'➖➖➖➖➖➖➖➖➖➖➖\n'
            f'ℹ️ <b>Информация о вас:</b>\n'
            f'🔑 <b>Логин:</b>@{message.chat.username}\n'
            f'<b>💳 ID:</b> <code>{message.chat.id}</code>\n'
            f'<b>💵 Покупок на сумму:</b> <code>0 руб</code>\n'
            f'➖➖➖➖➖➖➖➖➖➖➖')
    return text, markup


def historyOrders():
    markup = types.InlineKeyboardMarkup()
    button_main = types.InlineKeyboardButton("Главное меню", callback_data='main')
    markup.row(button_main)
    text = (f'В данном разделе будем выводить историю продаж\n'
            f'➖➖➖➖➖➖➖➖➖➖➖\n'
            f'10.03.2022 1шт <b>Куртка кожаная Fendi</b> 1620$ Сбербанк <code>+79999999999</code>\n'
            f'➖➖➖➖➖➖➖➖➖➖➖\n'
            f'09.03.2022 3шт <b>The Land of Legends</b> 2036₽ Тинькофф <code>+79999999999</code>\n'
            f'➖➖➖➖➖➖➖➖➖➖➖\n'
            f'09.03.2022 1шт <b>Астраган женский бежевый Valentino</b> 999$ Кредит <code>+79999999999</code>\n'
            f'➖➖➖➖➖➖➖➖➖➖➖')
    return text, markup


def paymentGateway():
    markup = types.InlineKeyboardMarkup()
    text = f'Выберите способ оплаты'
    types_payment = [[i['title'], i['id']] for i in api.get_payment_gateways()]
    for payment in types_payment:
        name, id = payment
        markup.row(types.InlineKeyboardButton(name, callback_data=f'order-paymentGateways_{id}'))
    return text, markup


def enter_product_id():
    markup = types.InlineKeyboardMarkup()
    text = f'Введите ID товара\nНапример: <code>340224712</code>'
    return text, markup


def product_info(chat_id, product):
    markup = types.InlineKeyboardMarkup()
    name = product["title"]
    price = query_insales.convert_price(chat_id, product["variants"][0]["base-price"])
    currency = query_db.get_currency_name(chat_id=chat_id)
    text = (f'ℹ️ <b>Информация о товаре:</b>\n'
            f'➖➖➖➖➖➖➖➖➖➖➖\n'
            f'<b>Название</b>: <code>{name}</code>\n'
            f'<b>Цена</b>: <code>{price} {currency}</code>\n'
            f'<b>Доступно на складе</b>: <code>{product["variants"][0]["quantity"]} шт</code>')
    button_current_price = types.InlineKeyboardButton("Оставить текущую цену",
                                                      callback_data=f'order-price_current_{price}')
    button_new_price = types.InlineKeyboardButton("Изменить цену", callback_data='order-price_new')
    photos = [types.InputMediaPhoto(i) for i in query_insales.get_photos(product['id'])]
    markup.row(button_current_price)
    markup.row(button_new_price)
    return text, markup, photos


def enter_product_price():
    markup = types.InlineKeyboardMarkup()
    text = f'Введите новую цену товара'
    return text, markup


def enter_product_quantity():
    markup = types.InlineKeyboardMarkup()
    text = f'Выберите количество'
    button_one = types.InlineKeyboardButton("1", callback_data='order-quantity_1')
    button_two = types.InlineKeyboardButton("2", callback_data='order-quantity_2')
    button_three = types.InlineKeyboardButton("3", callback_data='order-quantity_3')
    markup.row(button_one, button_two, button_three)
    return text, markup


def enter_client_name():
    markup = types.InlineKeyboardMarkup()
    text = f'Введите ФИО (полностью)'
    return text, markup


def enter_client_phone():
    markup = types.InlineKeyboardMarkup()
    text = (f'Введите сотовый клиента\n'
            f'Например: <code>79934055804</code>')
    return text, markup


def enter_client_mail():
    markup = types.InlineKeyboardMarkup()
    text = (f'Введите почту клиента\n'
            f'Например: <code>test@test.ru</code>')
    return text, markup


def create_order(chat_id):
    markup = types.InlineKeyboardMarkup()
    order = query_db.get_order_info(chat_id=chat_id)
    product_name = api.get_product(order.product_id)['title']
    currency = query_db.get_currency_name(chat_id=chat_id)
    payment_name = query_insales.get_name_paymentGateway(order.paymentGateway)
    text = (f'ℹ️ <b>Информация о заказе:</b>\n'
            f'➖➖➖➖➖➖➖➖➖➖➖\n'
            f'<b>Название</b>: <code>{product_name}</code>\n'
            f'<b>Цена</b>: <code>{order.price} {currency}</code>\n'
            f'<b>Тип оплаты</b>: <code>{payment_name}</code>\n'
            f'<b>Количество</b>: <code>{order.quantity}</code>\n'
            f'<b>Имя клиента</b>: <code>{order.client_name}</code>\n'
            f'<b>Сотовый клиента</b>: <code>+{order.client_phone}</code>\n'
            f'<b>Итого</b>: <code>{order.price * order.quantity} {currency}</code>')
    button_create_order = types.InlineKeyboardButton("Подтвердить заказ", callback_data='сreate')
    button_main = types.InlineKeyboardButton("Главное меню", callback_data='main')
    markup.row(button_create_order)
    markup.row(button_main)
    return text, markup


def url_on_payment(order):
    markup = types.InlineKeyboardMarkup()
    if order['payment-gateway-id'] in [2749759, 2814404]:
        text = (f'Ссылка на оплату\n'
                f'http://market-ra.ru/payments/external/{order["payment-gateway-id"]}/create?key={order["key"]}')

        qr = False
    elif order['payment-gateway-id'] in [2099426]:
        payment = query_insales.get_paymentGateway(2099426)
        text = "QR код для оплаты через мобильное приложение банка"
        qr_path = os.path.join(config.dir_path, 'utils', 'sbpqrcode')
        firstName, secondName, middleName = order["client"]["name"].split()
        qrcode.make(f'ST00012|Name=RaMarket'
                    f'|PersonalAcc={payment["settlement-account"]}|BankName={payment["bank-name"]}'
                    f'|BIC={payment["bin"]}|CorrespAcc={payment["correspondent-account"]}|PayeeINN={payment["inn"]}'
                    f'|LastName={secondName}|FirstName={firstName}|MiddleName={middleName}'
                    f'|Purpose=Оплата товара|Sum={int(order["total-price"])}00'
                    ).save(qr_path)
        qr = open(qr_path, 'rb')
    else:
        text = "Заказ успешно создан"
        qr = False
    return text, markup, qr
