from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, create_engine, update
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine('sqlite:///db/database.db', echo=True)


class User(Base):
    __tablename__ = 'data'

    id = Column(Integer, primary_key=True)
    name_in_chat = Column(String)
    id_user = Column(Integer)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)
    date = Column(String)
    age = Column(Integer)
    gender = Column(String)
    photo = Column(String)
    photo_for_chat = Column(String)
    latitude = Column(String)
    longitude = Column(String)
    description_user = Column(String)
    stack_of_partners = Column(String)

    def __init__(self, id, name_in_chat, id_user, first_name, last_name, username, date, age, gender, photo,
                 photo_for_chat, latitude, longitude, description_user, stack_of_partners):
        self.id = id
        self.name_in_chat = name_in_chat
        self.id_user = id_user
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.date = date
        self.age = age
        self.gender = gender
        self.photo = photo
        self.photo_for_chat = photo_for_chat
        self.latitude = latitude
        self.longitude = longitude
        self.description_user = description_user
        self.stack_of_partners = stack_of_partners

    def __repr__(self):
        return "<User('%s','%s', '%s')>" % (self.username, self.first_name, self.last_name)


Session = sessionmaker(bind=engine)
counter = 0


def finding_a_duplicate_entry_in_the_database(id_user: int) -> bool:
    """Поиск повторяющейся записи в БД"""
    session = Session()
    records = session.query(User).filter(User.id_user == id_user).all()
    return len(records) > 0


def write_to_the_database(id: int, name_in_chat: str, id_user: int, first_name: str, last_name: str, username: str, date: str, age: int, gender: str, photo: str, photo_for_chat: str, latitude: str, longitude: str, description_user: str, stack_of_partners: str):
    """Добавление записи в БД"""
    session = Session()
    new_user = User(id, name_in_chat, id_user, first_name, last_name, username, date, age, gender, photo, photo_for_chat, latitude, longitude, description_user, stack_of_partners)
    session.add(new_user)
    session.commit()


def update_record_in_the_database(name_in_chat: str, id_user: int, first_name: str, last_name: str, username: str, date: str, age: int, gender: str, photo: str, photo_for_chat: str, latitude: str, longitude: str, description_user: str, stack_of_partners: str):
    """Обновление записи пользователя"""
    session = Session()
    session.query(User).filter(User.id_user == id_user).update({'name_in_chat': name_in_chat, 'first_name': first_name, 'last_name': last_name, 'username': username, 'date': date, 'age': age, 'gender': gender, 'photo': photo, 'photo_for_chat': photo_for_chat, 'latitude': latitude, 'longitude': longitude, 'description_user': description_user, 'stack_of_partners': stack_of_partners})
    session.commit()


def update_stack_of_partners_in_record(id_user: int, stack_of_partners: str):
    """Обновление списка партнеров пользователя"""
    session = Session()
    session.query(User).filter(User.id_user == id_user).update({'stack_of_partners': stack_of_partners})
    session.commit()


def zeroing_stack_of_partners_in_record(id_user: int):
    """Обнуление списка партнеров пользователя"""
    session = Session()
    stack_of_partners = ''
    session.query(User).filter(User.id_user == id_user).update({'stack_of_partners': stack_of_partners})
    session.commit()


def extraction_stack_of_partners_from_record(id_user: int):
    """Извлечение списка партнеров пользователя"""
    session = Session()
    records = session.query(User).filter(User.id_user == id_user).all()
    if records[0].stack_of_partners == '':
        return []
    else:
        array = records[0].stack_of_partners.split()
        return array


def search_for_a_potential_partner(gen: str):
    """Поиск партнеров противоположного пола"""
    session = Session()
    records = session.query(User).filter(User.gender != gen).all()
    return records


def count_of_records_in_the_table():
    session = Session()
    records = session.query(User).all()
    return len(records) + 1
