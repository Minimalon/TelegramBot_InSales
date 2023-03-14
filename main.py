#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import telebot
from bs4 import BeautifulSoup
import insales.connection
import re
import os
from loguru import logger
from lib import forms, query_db, query_insales
import config

# ===============================================================
# Инициализация
bot = telebot.TeleBot(config.token)
if not os.path.exists(os.path.join(config.dir_path, 'logs')):
    os.makedirs(os.path.join(config.dir_path, 'logs'))
logger.add(os.path.join(config.dir_path, 'logs/debug.log'),
           level='DEBUG', rotation='10 MB', compression='zip')
# ===============================================================

logger.info("Начал работу")


@bot.callback_query_handler(func=lambda call: True)
@logger.catch()
def callback_query(call):
    request = call.data.split('_')
    logger.info(request)
    message = call.message
    try:
        bot.delete_message(message.chat.id, message.id)
        if request[0] == 'сreate':
            logger.info(f"Создание заказа --- {message.chat.first_name}")
            order = query_insales.create_order(message.chat.id)
            text, markup, qr = forms.url_on_payment(order)
            logger.info(text.split('\n'))
            if not qr:
                bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
            else:
                bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
                bot.send_photo(message.chat.id, qr)
            text, markup = forms.start()
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
        if request[0] == 'main':
            logger.info(f"'Главное меню' - {message.chat.first_name}")
            text, markup = forms.start()
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
        if 'order' in request[0]:
            if 'quantity' in request[0]:
                logger.info(f"quantity: {request[1]} - {message.chat.first_name}")
                query_db.update_order(chat_id=message.chat.id, quantity=request[1])
                text, markup = forms.enter_client_name()
                msg = bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
                query_db.update_order(chat_id=message.chat.id, messagefordelete=msg.message_id)
                bot.register_next_step_handler(msg, get_client_name)
            if 'price' in request[0]:
                delete_messages(message)
                if request[1] == 'current':
                    query_db.update_order(chat_id=message.chat.id, price=request[2])
                    text, markup = forms.enter_product_quantity()
                    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
                if request[1] == 'new':
                    text, markup = forms.enter_product_price()
                    msg = bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode='html')
                    query_db.update_order(chat_id=message.chat.id, messagefordelete=msg.message_id)
                    bot.register_next_step_handler(msg, get_price)
            if 'currency' in request[0]:
                logger.info(f"'Валюта[{request[1]}]' - {message.chat.first_name}")
                query_db.set_currency(chat_id=message.chat.id, first_name=message.chat.first_name, type=request[1])
                text, markup = forms.paymentGateway()
                bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
            if 'paymentGateway' in request[0]:
                logger.info(f"'Тип оплаты[{request[1]}]' - {message.chat.first_name}")
                currency = query_db.get_currency(message.chat.id)
                query_db.update_order(chat_id=message.chat.id, first_name=message.chat.first_name, currency=currency,
                                      paymentGateway=request[1])
                text, markup = forms.enter_product_id()
                msg = bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode='html')
                query_db.update_order(chat_id=message.chat.id, messagefordelete=msg.message_id)
                bot.register_next_step_handler(msg, get_product_id)
            if request[0] == 'order':
                logger.info(f"'Заказы' - {message.chat.first_name}")
                text, markup = forms.order()
                bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
        if request[0] == 'account':
            logger.info(f"'Личный кабинет' - {message.chat.first_name}")
            text, markup = forms.account(message)
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
        if request[0] == 'historyOrders':
            logger.info(f"'История заказов' - {message.chat.first_name}")
            text, markup = forms.historyOrders()
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
    except insales.connection.ApiError as ex:
        send_error(message, BeautifulSoup(str(ex), 'lxml').find('error').text)
    except Exception as ex:
        logger.exception(ex)


@bot.message_handler(commands=['start'])
def start(message):
    logger.info(f"Зашел {message.chat.first_name}")
    logger.info(message)
    text, markup = forms.start()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')


def send_error(message, text):
    logger.error(f"{text} --- {message.chat.first_name}")
    message_error = f"➖➖➖➖➖➖➖🚨ОШИБКА🚨➖➖➖➖➖➖➖"
    bot.send_message(message.chat.id, f"{message_error}\n<b>{text}</b>", parse_mode='html')
    text, markup = forms.start()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')


def delete_messages(message):
    ids = query_db.get_order_info(chat_id=message.chat.id).messagefordelete
    for msg in ids.split():
        bot.delete_message(message.chat.id, msg)


def get_product_id(message):
    try:
        delete_messages(message)
        product_id = message.text
        if re.findall('[0-9]*', product_id):
            product = query_insales.get_product(product_id)
            logger.info(f"'product_id': '{product_id}', 'name': '{product['title']}' - {message.chat.first_name}")
            query_db.update_order(chat_id=message.chat.id, product_id=product_id)
            text, markup, photos = forms.product_info(message.chat.id, product)
            msg = bot.send_media_group(message.chat.id, photos)
            message_ids = [str(i.message_id) for i in msg]
            query_db.update_order(chat_id=message.chat.id, messagefordelete=' '.join(message_ids))
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html', )
        else:
            logger.error(f"'product_id': '{product_id}' - {message.chat.first_name}")
            bot.send_message(message.chat.id, "Нужно ввести только цифры.\nПопробуйте снова.")
            text, markup = forms.paymentGateway()
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
    except insales.connection.ApiError as ex:
        send_error(message, BeautifulSoup(str(ex), 'lxml').find('error').text)
    except Exception as ex:
        logger.exception(f'{message.chat.first_name} --- {ex}')


def get_price(message):
    try:
        delete_messages(message)
        price = message.text
        if re.findall('[0-9]*', price):
            logger.info(f"'price': '{price}' - {message.chat.first_name}")
            product_id = query_db.get_order_info(chat_id=message.chat.id).product_id
            query_insales.update_price_on_product(product_id,
                                                  query_insales.convert_price_to_RUR(message.chat.id, price))
            query_db.update_order(chat_id=message.chat.id, price=price)
            text, markup = forms.enter_product_quantity()
            msg = bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
            query_db.update_order(chat_id=message.chat.id, messagefordelete=msg.message_id)
        else:
            logger.error(f"'price': '{price}' - {message.chat.first_name}")
            msg_error = bot.send_message(message.chat.id, "Нужно ввести только цифры.\nПопробуйте снова.")
            text, markup = forms.enter_product_price()
            msg = bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
            query_db.update_order(chat_id=message.chat.id,
                                  messagefordelete="{} {}".format(msg.message_id, msg_error.message_id))
            bot.register_next_step_handler(msg, get_price)
    except insales.connection.ApiError as ex:
        send_error(message, BeautifulSoup(str(ex), 'lxml').find('error').text)
    except Exception as ex:
        logger.exception(f'{message.chat.first_name} --- {ex}')


def get_client_name(message):
    try:
        delete_messages(message)
        client_name = message.text
        if len(client_name.split()) == 3:
            logger.info(f"'client_name': '{client_name}' - {message.chat.first_name}")
            query_db.update_order(chat_id=message.chat.id, client_name=client_name)
            text, markup = forms.enter_client_phone()
            msg = bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
            query_db.update_order(chat_id=message.chat.id, messagefordelete=msg.message_id)
            bot.register_next_step_handler(msg, get_client_phone)
        else:
            logger.error(f"'client_name': '{client_name}' - {message.chat.first_name}")
            text = f"ФИО состоит из 3 слов, а вы ввели {len(client_name.split())} слова\nПопробуйте снова."
            msg_error = bot.send_message(message.chat.id, text)
            text, markup = forms.enter_client_name()
            msg = bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
            query_db.update_order(chat_id=message.chat.id,
                                  messagefordelete="{} {}".format(msg.message_id, msg_error.message_id))
            bot.register_next_step_handler(msg, get_client_name)
    except insales.connection.ApiError as ex:
        send_error(message, BeautifulSoup(str(ex), 'lxml').find('error').text)
    except Exception as ex:
        logger.exception(f'{message.chat.first_name} --- {ex}')


def get_client_phone(message):
    try:
        delete_messages(message)
        client_phone = ''.join(re.findall(r'[0-9]*', message.text))
        if re.findall('[0-9]{11}', client_phone):
            logger.info(f"'client_phone': '{client_phone}' - {message.chat.first_name}")
            query_db.update_order(chat_id=message.chat.id, client_phone=client_phone)
            text, markup = forms.create_order(message.chat.id)
            msg = bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
            query_db.update_order(chat_id=message.chat.id, messagefordelete=msg.message_id)
        else:
            logger.error(f"'client_phone': '{client_phone}' - {message.chat.first_name}")
            text = ("Нужно ввести только цифры, номер должен состоят из 11 цифр, номер должен начинаться на 7\n"
                    "Например: <code>79934055805</code>\n"
                    "Попробуйте снова.")
            msg_error = bot.send_message(message.chat.id, text, parse_mode='html')
            text, markup = forms.enter_client_phone()
            msg = bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
            query_db.update_order(chat_id=message.chat.id,
                                  messagefordelete="{} {}".format(msg.message_id, msg_error.message_id))
            bot.register_next_step_handler(msg, get_client_phone)
    except insales.connection.ApiError as ex:
        send_error(message, BeautifulSoup(str(ex), 'lxml').find('error').text)
    except Exception as ex:
        logger.exception(f'{message.chat.first_name} --- {ex}')


# def get_client_mail(message):
#     try:
#         client_mail = message.text
#         if re.findall('@', client_mail):
#             logger.info(f"'client_mail': '{client_mail}' - {message.chat.first_name}")
#             query_db.update_order(chat_id=message.chat.id, client_mail=client_mail)
#             text, markup = forms.create_order(message.chat.id)
#             bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
#         else:
#             logger.error(f"'client_mail': '{client_mail}' - {message.chat.first_name}")
#             bot.send_message(message.chat.id, "Нужно ввести почту клиента.\nПопробуйте снова.")
#             text, markup = forms.enter_client_mail()
#             msg = bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='html')
#             bot.register_next_step_handler(msg, get_client_mail)
#     except Exception as ex:
#         logger.exception(f'{message.chat.first_name} --- {ex}')


bot.polling()
