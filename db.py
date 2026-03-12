import supabase
from models import Wishlist, User, engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
Session=sessionmaker(bind=engine)
def user_save(user_id,name,cc,l):
    session=Session()
    user=session.query(User).filter_by(id=user_id).first()
    if not user:
        user=User(id=user_id,name=name,cc=cc,l=l)
        session.add(user)
        session.commit()
    else:
        user.cc=cc
        user.l=l
        user.name=name
        session.commit()
def get_settings(user_id):
    session=Session()
    user=session.query(User).filter_by(id=user_id).first()
    if user:
        return {"cc":user.cc,
                "l":user.l,
                "dl":user.discount_limit,
                "name":user.name}
    else:
        return None
def wishlist_add(user_id, game_id, game_name):
    session = Session()
    game = session.query(Wishlist).filter_by(user_id=user_id,game_id=game_id).first()
    if game:
        return False
    new_game = Wishlist(
        user_id=user_id,
        game_id=game_id,
        game_name=game_name)
    session.add(new_game)
    session.commit()
    return True
def wishlist_delete(user_id,game_id):
    session=Session()
    game=session.query(Wishlist).filter_by(game_id=game_id,user_id=user_id).first()
    if game:
        session.delete(game)
        session.commit()
        return True
    else:
        return False
def get_wishlist(user_id):
    session=Session()
    games=session.query(Wishlist).filter_by(user_id=user_id).all()
    if games:
        return games
def get_users():
    session=Session() 
    users=session.query(User).all()
    return users   
def set_discount(user_id, discount_number):
    session = Session()
    user = session.query(User).filter_by(id=user_id).first()
    if user:
        user.discount_limit = discount_number
        session.commit()
        return True
    return False
def get_usercount():
    session = Session()
    return session.query(func.count(User.id)).scalar()
def get_gamecount():
    session = Session()
    return session.query(func.count(Wishlist.id)).scalar()
def get_most_popular_game():
    session = Session()
    popular_game=session.query(Wishlist.game_name,func.count(Wishlist.game_id).label("count_")).group_by(Wishlist.game_id,Wishlist.game_name).order_by(func.count(Wishlist.game_id).desc()).first()
    return {"name": popular_game.game_name,
            "count":popular_game.count_}
def get_allstats():
    return{"users": get_usercount(),
           "games": get_gamecount(),
           "populargame": get_most_popular_game()}
#Сделать вывод всех команд при /start и попытатся доделать mini-app



