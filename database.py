from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()
engine = create_engine('sqlite:///transactions.db')
Session = sessionmaker(bind=engine)
session = Session()

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    type = Column(String)
    category = Column(String)
    amount = Column(Float)
    date = Column(Date, default=datetime.date.today)
    note = Column(String)

Base.metadata.create_all(engine)

def add_transaction(type, category, amount, note=""):
    new_txn = Transaction(type=type, category=category, amount=amount, note=note)
    session.add(new_txn)
    session.commit()

def get_all_transactions():
    return session.query(Transaction).all()
