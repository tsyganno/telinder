from aiogram.dispatcher.filters.state import State, StatesGroup


class Form(StatesGroup):
    captcha = State()
    name = State()
    user_photo = State()
    age = State()
    gender = State()
    intercourse = State()
