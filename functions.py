import math
import csv
from multicolorcaptcha import CaptchaGenerator
from aiogram import types


def create_list_of_cities():
    dict_city = {}
    with open('city.csv', 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for el in reader:
            city, lat, lon = el[9], el[20], el[21]
            dict_city[city] = (lat, lon)
    return dict_city


def keyboard_submit_edit():
    """ Создание кнопки 'Обновить профиль' """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("/Обновить_профиль")
    return markup


def keyboard_submit_search_partner():
    """ Создание кнопки 'Обновить профиль' и 'Начнем искать пару?' """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Начнем искать пару?")
    markup.add("/Обновить_профиль")
    return markup


def keyboard_submit_gender():
    """ Создание кнопки 'Обновить профиль' и 'выбор пола' """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Мужчина", "Женщина")
    markup.add('/Обновить_профиль')
    return markup


def generate_captcha():
    """ Создание капчи """
    CAPCTHA_SIZE_NUM = 2
    generator = CaptchaGenerator(CAPCTHA_SIZE_NUM)
    captcha = generator.gen_captcha_image(difficult_level=3)
    math_captcha = generator.gen_math_captcha_image(difficult_level=2)
    image = captcha.image
    math_image = math_captcha.image
    math_equation_string = math_captcha.equation_str
    math_equation_result = math_captcha.equation_result
    image.save("captcha_image.png", "png")
    math_image.save("captcha_image.png", "png")
    return math_equation_string, math_equation_result


def examination_captcha(user_captcha, captcha_string, captcha_math):
    """ Проверка капчи """
    try:
        sign = ''
        for el in user_captcha:
            if not el.isdigit():
                sign += el
        left_part, right_part = user_captcha.split(sign)
        dict_sign = {'-': int(left_part) - int(right_part), '+': int(left_part) + int(right_part), '*': int(left_part) + int(right_part), '/': int(left_part) + int(right_part)}
        digit = dict_sign[sign]
        return user_captcha == captcha_string and str(digit) == captcha_math
    except ValueError:
        return False


def restart_captcha():
    """ Создание новой капчи """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("/Загрузить_новую_капчу?")
    return markup


def search_geo(cities: dict, locality: str):
    """ Поиск координат геолокации пользователя """
    try:
        for key in cities.keys():
            if locality.lower() == key.lower():
                latitude, longitude = cities[key][0], cities[key][1]
                return latitude, longitude
    except AttributeError:
        return None


def found_city_radius(latitude, longitude):
    """Поиск всех локаций в радиусе от заданной локации"""

    dist = int(50)  # дистанция 50 км
    mylon = float(longitude)  # долгота
    mylat = float(latitude)  # широта
    lon1 = mylon - dist / abs(math.cos(math.radians(mylat)) * 111.0)  # 1 градус широты = 111 км
    lon2 = mylon + dist / abs(math.cos(math.radians(mylat)) * 111.0)
    lat1 = mylat - (dist / 111.0)
    lat2 = mylat + (dist / 111.0)
    return lon1, lon2, lat1, lat2


def check_for_none(username):
    if username is None:
        result = None
    else:
        result = f'@{username}'
    return result
