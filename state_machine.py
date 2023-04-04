from aiogram.dispatcher.filters.state import State, StatesGroup


class Form(StatesGroup):
    captcha = State()
    name = State()
    locality = State()
    age = State()
    gender = State()
    description = State()
    user_photo = State()
    intercourse = State()
