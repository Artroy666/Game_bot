from sqlalchemy import create_engine,Column,Integer,Text,ForeignKey
from sqlalchemy.orm import relationship,declarative_base,sessionmaker
database_url="postgresql://postgres.qheqyynusrnuphashcrh:m4bsYQ0ladlGS4Fm@aws-1-eu-central-1.pooler.supabase.com:6543/postgres"
engine=create_engine(database_url)
Base=declarative_base()
class User(Base):
    __tablename__="user"
    id=Column(Integer,primary_key=True)
    name=Column(Text)
    cc=Column(Text)
    l=Column(Text)
    discount_limit=Column(Integer,default=1)
    wishlist=relationship("Wishlist",back_populates="user")
class Wishlist(Base):
    __tablename__="wishlist"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"))
    game_id=Column(Integer)
    game_name=Column(Text)
    user=relationship("User",back_populates="wishlist")
Base.metadata.create_all(engine)