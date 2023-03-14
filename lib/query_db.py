from sqlalchemy import *
from sqlalchemy.orm import *
import lib.database

engine = create_engine("mysql+pymysql://root:Csminimal$23662@127.0.0.1:3306/insales?charset=utf8mb4")
Session = sessionmaker(bind=engine)


def get_currency(chat_id):
    with Session() as session:
        DB = lib.database.Currency
        return session.query(DB).filter(DB.chat_id == str(chat_id)).first().type


def set_currency(**kwargs):
    with Session() as session:
        DB = lib.database.Currency
        SN = session.query(DB).filter(DB.chat_id == str(kwargs["chat_id"])).first()
        if SN is None:
            if len(kwargs) == len([v for k, v in kwargs.items() if v]):
                SN = DB(**kwargs)
                session.add(SN)
        else:
            session.query(DB).filter(DB.chat_id == str(kwargs["chat_id"])) \
                .update({"type": kwargs["type"]}, synchronize_session='fetch')
        session.commit()


def update_order(**kwargs):
    with Session() as session:
        DB = lib.database.Orders
        SN = session.query(DB).filter(DB.chat_id == str(kwargs["chat_id"])).first()
        if SN is None:
            if len(kwargs) == len([v for k, v in kwargs.items() if v]):
                SN = DB(**kwargs)
                session.add(SN)
        else:
            session.query(DB).filter(DB.chat_id == str(kwargs["chat_id"])).update(kwargs, synchronize_session='fetch')
        session.commit()


def create_historyOrder(**kwargs):
    with Session() as session:
        DB = lib.database.HistoryOrders
        session.add(DB(**kwargs))
        session.commit()


def get_order_info(**kwargs):
    with Session() as session:
        DB = lib.database.Orders
        return session.query(DB).filter(DB.chat_id == str(kwargs["chat_id"])).first()


def get_currency_name(**kwargs):
    with Session() as session:
        DB = lib.database.Orders
        order = session.query(DB).filter(DB.chat_id == str(kwargs["chat_id"])).first()
        if order.currency == 'RUR':
            currency = 'руб'
        elif order.currency == 'USD':
            currency = '$'
        else:
            currency = ''
        return currency
