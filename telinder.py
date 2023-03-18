from os import getenv
from random import choice
from dotenv import load_dotenv

from multicolorcaptcha import CaptchaGenerator

import logging
import time
import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types.input_file import InputFile

from db import Sql_lite
from stack import Partner, StackCaptcha

load_dotenv()

logging.basicConfig(level=logging.INFO)

API_TOKEN = getenv('BOT_TOKEN')

bot = Bot(token=API_TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

db = Sql_lite()
arr = Partner()
arr_cap = StackCaptcha()
counter = 0


class Form(StatesGroup):
    captcha = State()
    name = State()
    user_photo = State()
    age = State()
    gender = State()
    intercourse = State()


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


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    """ Прохождение капчи """
    captcha_string, captcha_math = generate_captcha()
    arr_cap.array_captcha.append(captcha_string)
    arr_cap.array_captcha.append(captcha_math)
    path_captcha = InputFile('captcha_image.png')
    await Form.captcha.set()
    await message.reply("Привет! Чтобы использовать этот бот, тебе необходимо пройти испытание капчей =)\nПроходя это испытание, ты подтверждаешь, что тебе уже есть 18 лет.\nОтправь мне цифры изображенные на картинке =)")
    await bot.send_photo(chat_id=message.chat.id, photo=path_captcha)


@dp.message_handler(state='*', commands=['Загрузить_новую_капчу?'])
async def process_name(message: types.Message):
    """ Создание новой капчи """
    captcha_string, captcha_math = generate_captcha()
    arr_cap.array_captcha.append(captcha_string)
    arr_cap.array_captcha.append(captcha_math)
    path_captcha = InputFile('captcha_image.png')
    await Form.captcha.set()
    await message.reply("Отправь мне цифры и символы, в той же последовательности, которые изображены на картинке =)")
    await bot.send_photo(chat_id=message.chat.id, photo=path_captcha)


@dp.message_handler(state=Form.captcha)
async def process_name(message: types.Message):
    """ Прохождение капчи """
    user_captcha = message.text
    if examination_captcha(user_captcha, arr_cap.array_captcha[0], arr_cap.array_captcha[1]) is True:
        await Form.next()
        await message.reply("Как тебя зовут?")
    else:
        arr_cap.array_captcha = []
        await message.reply("Что-то пошло не так...\nПоробуйте снова или загрузите новую капчу.", reply_markup=restart_captcha())


@dp.message_handler(state='*', commands=['Сброс'])
async def process_name(message: types.Message):
    """ Возврат в исходное состояние, в точку входа в разговор """
    await Form.name.set()
    await message.reply("Как тебя зовут?")


@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    """ Имя пользователя процесса """
    async with state.proxy() as data:
        data['name'] = message.text
    await Form.next()
    await message.reply("Добавьте свое фото", reply_markup=keyboard_submit_edit())


@dp.message_handler(lambda message: not message.photo, state=Form.user_photo)
async def process_photo_invalid(message: types.Message):
    """ Если пользователь загружает не фото """
    return await message.reply("Фотография не найдена в сообщении =(\nЗагрузи свою фотку")


@dp.message_handler(content_types=['photo'], state=Form.user_photo)
async def process_photo(message: types.Message, state: FSMContext):
    """ Фото пользователя процесса """
    async with state.proxy() as data:
        document_id = message.photo[-1].file_id
        file_info = await bot.get_file(document_id)
        path = f'http://api.telegram.org/file/bot{API_TOKEN}/{file_info.file_path}'
        data['user_photo'] = [path, document_id]
    await Form.next()
    # await bot.send_photo(chat_id=message.chat.id, photo=message.photo[-1].file_id)
    await message.reply("Сколько тебе лет?", reply_markup=keyboard_submit_edit())


@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.age)
async def process_age_invalid(message: types.Message):
    """ Если возраст у пользователя неверный """
    return await message.reply("Возраст должен быть числом.\nСколько тебе лет? (только цифры)")


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.age)
async def process_age(message: types.Message, state: FSMContext):
    """ Выбор взраста пользователем """
    await Form.next()
    if int(message.text) < 18:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add('/Сброс')
        await message.reply("Вам должно быть больше 18 лет!\nУдалите бот, если вам меньше 18 лет, в противном случае нажмите 'Сброс'", reply_markup=markup)
    else:
        await state.update_data(age=int(message.text))
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add("Мужчина", "Женщина")
        markup.add('/Сброс')
        await message.reply("Какого Вы пола?", reply_markup=markup)


@dp.message_handler(lambda message: message.text not in ["Мужчина", "Женщина"], state=Form.gender)
async def process_gender_invalid(message: types.Message):
    """В этом примере пол должен быть одним из: Мужской или Женский """
    return await message.reply("Плохое гендерное имя. Выберите свой пол с клавиатуры.")


@dp.message_handler(state=Form.gender)
async def process_gender(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        global counter
        data['gender'] = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add("Начнем искать пару? Нажимай скорее =)")
        markup.add("/Сброс")
        counter += 1
        if db.finding_a_duplicate_entry_in_the_database(message.from_user.id) is True:
            db.update_record_in_the_database(
                name_in_chat=data['name'],
                id_user=message.from_user.id,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                username=message.from_user.username,
                date=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                age=data['age'],
                gender=data['gender'],
                photo=data['user_photo'][0],
                photo_for_chat=data['user_photo'][1],
            )
        else:
            db.write_to_the_database(
                id=counter,
                name_in_chat=data['name'],
                id_user=message.from_user.id,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                username=message.from_user.username,
                date=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                age=data['age'],
                gender=data['gender'],
                photo=data['user_photo'][0],
                photo_for_chat=data['user_photo'][1],
            )
        await bot.send_message(
            message.chat.id,
            md.text(
                md.text('Ваше имя', md.bold(data['name'])),
                md.text('Возраст:', md.code(data['age'])),
                md.text('Пол:', data['gender']),
                md.text('Профиль заполнен. Теперь можно найти себе пару =)'),
                md.text('Для изменения профиля нажмите /Сброс.'),
                sep='\n',
            ),
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN,
        )
    await Form.next()


@dp.message_handler(state=Form.intercourse)
async def process_age(message: types.Message, state: FSMContext):
    """ Выбор партнера """
    async with state.proxy() as data:
        # markup = types.ReplyKeyboardRemove()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add("Начнем искать пару?")
        markup.add("/Сброс")
        try:
            array_partners = db.search_for_a_potential_partner(data['gender'])
            while True:
                partner = choice(array_partners)
                if partner not in arr.array:
                    if partner[5] is None:
                        await bot.send_message(
                            message.chat.id,
                            md.text(
                                md.text(f'Зовут: {str(partner[1])}'),
                                md.text(f'Возраст: {str(partner[7])}'),
                                md.text(f'Username для поиска в Telegram: не существует'),
                                sep='\n',
                            ),
                            reply_markup=markup,
                            parse_mode=ParseMode.MARKDOWN,
                        )
                        await bot.send_photo(chat_id=message.chat.id, photo=partner[10])
                        arr.array.append(partner)
                        break
                    else:
                        await bot.send_message(
                            message.chat.id,
                            md.text(
                                md.text(f'Зовут: {str(partner[1])}'),
                                md.text(f'Возраст: {str(partner[7])}'),
                                md.text(f'Username для поиска в Telegram: {partner[5]}'),
                                sep='\n',
                            ),
                            reply_markup=markup,
                            parse_mode=ParseMode.MARKDOWN,
                        )
                        await bot.send_photo(chat_id=message.chat.id, photo=partner[10])
                        arr.array.append(partner)
                        break
                else:
                    await message.reply("Пары закончились. Обновите профиль (/Сброс) и начните искать по новому =)", reply_markup=markup)
                    break
        except:
            pass

    # await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

