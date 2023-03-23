from multicolorcaptcha import CaptchaGenerator
from aiogram import types


def keyboard_submit_edit():
    """ Создание кнопки Сброса """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("/Сброс")
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
