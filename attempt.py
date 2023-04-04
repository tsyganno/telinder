from os import getenv
from random import choice
from dotenv import load_dotenv

import logging
import time
import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types.input_file import InputFile

from db_sqlalchemy import write_to_the_database, finding_a_duplicate_entry_in_the_database, \
    update_record_in_the_database, search_for_a_potential_partner, count_of_records_in_the_table, \
    update_stack_of_partners_in_record, extraction_stack_of_partners_from_record, zeroing_stack_of_partners_in_record, delete_record
from stack import StackCaptcha
from state_machine import Form
from functions import keyboard_submit_edit, generate_captcha, examination_captcha, restart_captcha, search_geo, \
    found_city_radius, create_list_of_cities, check_for_none, keyboard_submit_search_partner, keyboard_submit_gender, keyboard_submit_edit_delete

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_TOKEN = getenv('BOT_TOKEN')

bot = Bot(token=API_TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

arr_cap = StackCaptcha()
dict_city = create_list_of_cities()

PRICE = types.LabeledPrice(label="Подписка на 1 месяц", amount=500*100)  # в копейках (руб)


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
    if examination_captcha(user_captcha, arr_cap.array_captcha[-2], arr_cap.array_captcha[-1]) is True:
        await Form.next()
        await message.reply('Как тебя зовут?')
    else:
        await message.reply("Что-то пошло не так...\nПоробуйте снова или загрузите новую капчу.", reply_markup=restart_captcha())


@dp.message_handler(state='*', commands=['Обновить_профиль'])
async def process_name(message: types.Message):
    """ Возврат в исходное состояние, в точку входа в разговор """
    await Form.name.set()
    await message.reply("Как тебя зовут?")


@dp.message_handler(state='*', commands=['Удалить_профиль'])
async def process_name(message: types.Message):
    """ Возврат в исходное состояние, в точку входа в разговор, удаление профиля из бд"""
    delete_record(message.from_user.id)
    await Form.name.set()
    await message.reply("Вы удалили свой профиль из базы данных, теперь никто вас не найдет...\nЧтобы снова начать искать свою любовь, заполните свой профиль.\n Как тебя зовут?", reply_markup=keyboard_submit_edit())


@dp.message_handler(lambda message: message.text, state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    """ Имя пользователя процесса """
    async with state.proxy() as data:
        data['name'] = message.text
    zeroing_stack_of_partners_in_record(message.from_user.id)
    await Form.next()
    await message.reply("Введите название своего населенного пункта", reply_markup=keyboard_submit_edit())


@dp.message_handler(state=Form.locality)
async def process_name(message: types.Message, state: FSMContext):
    """ Населенный пункт пользователя процесса """
    if search_geo(dict_city, message.text) is not None:
        async with state.proxy() as data:
            data['local_geo'] = search_geo(dict_city, message.text)
            found_city_radius(data['local_geo'][0], data['local_geo'][1])
        await Form.next()
        await message.reply("Сколько тебе лет?", reply_markup=keyboard_submit_edit())
    else:
        await message.reply("Введите корректное название населенного пункта", reply_markup=keyboard_submit_edit())


@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.age)
async def process_age_invalid(message: types.Message):
    """ Если возраст у пользователя неверный """
    return await message.reply("Возраст должен быть числом.\nСколько тебе лет? (только цифры)")


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.age)
async def process_age(message: types.Message, state: FSMContext):
    """ Выбор возраста пользователем """
    if int(message.text) < 18:
        await message.reply("Вам должно быть больше 18 лет!\nУдалите бот, если вам меньше 18 лет, в противном случае нажмите 'Обновить_профиль'", reply_markup=keyboard_submit_edit())
    elif int(message.text) >= 100:
        await message.reply("Наверное вам не стоит искать себе пару, пощадите себя =(\nПопробуйте снова.", reply_markup=keyboard_submit_edit())
    elif 60 < int(message.text) < 100:
        await Form.next()
        await state.update_data(age=int(message.text))
        await message.reply("А ты бодрый старикашка или старушка =) Какого Вы пола?", reply_markup=keyboard_submit_gender())
    else:
        await Form.next()
        await state.update_data(age=int(message.text))
        await message.reply("Какого Вы пола?", reply_markup=keyboard_submit_gender())


@dp.message_handler(lambda message: message.text not in ["Мужчина", "Женщина"], state=Form.gender)
async def process_gender_invalid(message: types.Message):
    """В этом примере пол должен быть одним из: Мужской или Женский """
    return await message.reply("Плохое гендерное имя. Выберите свой пол с клавиатуры.")


@dp.message_handler(lambda message: message.text, state=Form.gender)
async def process_gender(message: types.Message, state: FSMContext):
    """ Выбор пола пользователем """
    async with state.proxy() as data:
        data['gender'] = message.text
    await Form.next()
    await message.reply("Расскажите о себе.", reply_markup=keyboard_submit_edit())


@dp.message_handler(lambda message: message.text, state=Form.description)
async def process_gender(message: types.Message, state: FSMContext):
    """ Описание пользователя """
    async with state.proxy() as data:
        data['description'] = message.text
    await Form.next()
    await message.reply("Добавьте свое фото.", reply_markup=keyboard_submit_edit())


@dp.message_handler(lambda message: message.photo, state=Form.user_photo)
async def process_photo_invalid(message: types.Message):
    """ Если пользователь загружает не фото """
    return await message.reply("Фотография не найдена в сообщении =(\nЗагрузи свою фотку")


@dp.message_handler(content_types=['document'], state=Form.user_photo)
async def process_photo_invalid(message: types.Message):
    """ Если пользователь загружает файл """
    return await message.reply("Вы отправили файл. Попробуйте отправить фото, предварительно сжав его.")


@dp.message_handler(content_types=['voice'], state=Form.user_photo)
async def process_photo_invalid(message: types.Message):
    """ Если пользователь загружает аудио """
    return await message.reply("Вы отправили аудио. Попробуйте отправить фото, предварительно сжав его.")


@dp.message_handler(content_types=['video_note', 'video'], state=Form.user_photo)
async def process_photo_invalid(message: types.Message):
    """ Если пользователь загружает видео """
    return await message.reply("Вы отправили видео. Попробуйте отправить фото, предварительно сжав его.")


@dp.message_handler(content_types=['photo'], state=Form.user_photo)
async def process_photo(message: types.Message, state: FSMContext):
    """ Фото пользователя процесса """
    async with state.proxy() as data:
        global counter
        document_id = message.photo[-1].file_id
        file_info = await bot.get_file(document_id)
        path = f'http://api.telegram.org/file/bot{API_TOKEN}/{file_info.file_path}'
        data['user_photo'] = [path, document_id]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add("Начнем искать пару? Нажимай скорее =)")
        markup.add("/Обновить_профиль")
        counter = count_of_records_in_the_table()
        if finding_a_duplicate_entry_in_the_database(message.from_user.id) is True:
            username = check_for_none(message.from_user.username)
            update_record_in_the_database(
                name_in_chat=data['name'],
                id_user=message.from_user.id,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                username=username,
                date=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                age=data['age'],
                gender=data['gender'],
                photo=data['user_photo'][0],
                photo_for_chat=data['user_photo'][1],
                latitude=data['local_geo'][0],
                longitude=data['local_geo'][1],
                description_user=data['description'],
                stack_of_partners='',
            )
        else:
            username = check_for_none(message.from_user.username)
            write_to_the_database(
                id=counter,
                name_in_chat=data['name'],
                id_user=message.from_user.id,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                username=username,
                date=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                age=data['age'],
                gender=data['gender'],
                photo=data['user_photo'][0],
                photo_for_chat=data['user_photo'][1],
                latitude=data['local_geo'][0],
                longitude=data['local_geo'][1],
                description_user=data['description'],
                stack_of_partners='',
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
        try:
            potential_partners = search_for_a_potential_partner(data['gender'])
            logger.info(f'ПАРТНЕРЫ !!! {potential_partners}')
            lon1, lon2, lat1, lat2 = found_city_radius(data['local_geo'][0], data['local_geo'][1])
            array_partners = list(filter(lambda x: lat1 < float(x.latitude) < lat2 and lon1 < float(x.longitude) < lon2, potential_partners))
            while True:
                partner = choice(array_partners)
                array = extraction_stack_of_partners_from_record(message.from_user.id)
                # logger.info(f'ПАРТНЕРЫ STACK {partner.id_user}')
                # logger.info(f'STACK {array}')
                if str(partner.id_user) not in array:
                    if partner.username is None:
                        await bot.send_message(
                            message.chat.id,
                            md.text(
                                md.text(f'Зовут: {partner.name_in_chat}'),
                                md.text(f'Возраст: {partner.age}'),
                                md.text(f'Username для поиска в Telegram: не существует'),
                                sep='\n',
                            ),
                            reply_markup=keyboard_submit_search_partner(),
                            parse_mode=ParseMode.MARKDOWN,
                        )
                        await bot.send_photo(chat_id=message.chat.id, photo=partner.photo_for_chat)
                        update_stack_of_partners_in_record(message.from_user.id, str(partner.id_user) + ' ')
                        break
                    else:
                        await bot.send_message(
                            message.chat.id,
                            md.text(
                                md.text(f'Зовут: {partner.name_in_chat}'),
                                md.text(f'Возраст: {partner.age}'),
                                md.text(f'Username для поиска в Telegram: {partner.username}'),
                                md.text(f'Описание: {partner.description_user}'),
                                sep='\n',
                            ),
                            reply_markup=keyboard_submit_search_partner(),
                            parse_mode=ParseMode.MARKDOWN,
                        )
                        await bot.send_photo(chat_id=message.chat.id, photo=partner.photo_for_chat)
                        update_stack_of_partners_in_record(message.from_user.id, str(partner.id_user) + ' ')
                        break
                else:
                    await message.reply("Пары закончились. Обновите профиль (/Обновить_профиль) и начните искать по новому =)\nТакже вы можете удалить свой профиль (/Удалить_профиль)", reply_markup=keyboard_submit_edit_delete())
                    break
        except:
            # logger.exception('Ошибка!!!')
            await message.reply("Ошибка, трудно =(", reply_markup=keyboard_submit_search_partner())


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)