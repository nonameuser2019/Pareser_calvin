from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy.orm import mapper
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Text, String, Float


Base = declarative_base()
class Calvin(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True)
    product_name = Column(String)
    price = Column(Float)
    price_sale = Column(String)
    discount = Column(String)
    size = Column(String)
    color = Column(String)
    image_name = Column(String)
    details = Column(String)
    universal_id = Column(String)
    category = Column(String)
    all_color = Column(String)
    url = Column(String)

    def __init__(self, product_name, price, price_sale, discount, size, color, image_name, details, universal_id, category, all_color, url):
        self.product_name = product_name
        self.price = price
        self.price_sale = price_sale
        self.discount = discount
        self.size = size
        self.color = color
        self.image_name = image_name
        self.details = details
        self.universal_id = universal_id
        self.category = category
        self.all_color = all_color
        self.url = url

    def __repr__(self):
        return "CData '%s'" % (self.url)

class CalvinPrice(Base):

    __tablename__ = "price_product"
    id = Column(Integer, primary_key=True)
    price = Column(Float)
    price_sale = Column(String)
    discount = Column(String)
    url = Column(String)

    def __init__(self, price, price_sale, discount, url):
        self.price = price
        self.price_sale = price_sale
        self.discount = discount
        self.url = url

db_engine = create_engine("sqlite:///calvin.db", echo=True)
Base.metadata.create_all(db_engine)




