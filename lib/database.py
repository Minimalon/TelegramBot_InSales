import sqlalchemy.orm
from sqlalchemy import create_engine, Integer, String, \
    Column

engine = create_engine("mysql+pymysql://root:Csminimal$23662@127.0.0.1:3306/insales?charset=utf8mb4")
Base = sqlalchemy.orm.declarative_base()


class Currency(Base):
    __tablename__ = 'currency'
    chat_id = Column(String(50), nullable=False, primary_key=True)
    first_name = Column(String(50), nullable=False)
    type = Column(String(10), nullable=False)

    def __init__(self, chat_id, first_name, type):
        self.chat_id = chat_id
        self.first_name = first_name
        self.type = type

    def update(self, **kwargs):
        if self.chat_id != kwargs['chat_id']:
            self.chat_id = kwargs['chat_id']
        if self.first_name != kwargs['first_name']:
            self.first_name = kwargs['first_name']
        if self.type != kwargs['type']:
            self.type = kwargs['type']


class Orders(Base):
    __tablename__ = 'orders'
    chat_id = Column(String(50), nullable=False, primary_key=True)
    first_name = Column(String(50), nullable=False)
    paymentGateway = Column(String(50), nullable=False)
    product_id = Column(String(50))
    price = Column(Integer)
    quantity = Column(Integer)
    currency = Column(String(10))
    client_name = Column(String(100))
    client_phone = Column(String(20))
    client_mail = Column(String(100))
    messagefordelete = Column(String(300))


class HistoryOrders(Base):
    __tablename__ = 'historyOrders'
    order_id = Column(String(50), nullable=False, primary_key=True)
    chat_id = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    paymentGateway = Column(String(50), nullable=False)
    product_id = Column(String(50))
    price = Column(Integer)
    quantity = Column(Integer)
    currency = Column(String(10))
    client_name = Column(String(100))
    client_phone = Column(String(20))
    client_mail = Column(String(100))


Base.metadata.create_all(engine)
