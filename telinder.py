from os import getenv
from dotenv import load_dotenv
load_dotenv()

import logging

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor

logging.basicConfig(level=logging.INFO)

API_TOKEN = getenv('BOT_TOKEN')


bot = Bot(token=API_TOKEN)

# Например, используйте простой MemoryStorage для Dispatcher.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Состояния
class Form(StatesGroup):
    name = State()  # Будет представлен в хранилище как «Форма: имя».
    user_photo = State()  # Будет представлен в хранилище как «Форма: фото».
    age = State()  # Будет представлен в хранилище как «Форма: возраст».
    gender = State()  # Будет представлен в хранилище как «Форма: пол».


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    """
    Точка входа в разговор
    """
    # Установить состояние
    await Form.name.set()

    await message.reply("Всем привет! Как тебя зовут?")


# Вы можете использовать состояние '*', если вам нужно обрабатывать все состояния
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Разрешить пользователю отменять любое действие
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Отменить состояние и сообщить об этом пользователю
    await state.finish()
    # И убрать клавиатуру (на всякий случай)
    await message.reply('Отменено.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    """
    Имя пользователя процесса
    """
    async with state.proxy() as data:
        data['name'] = message.text

    await Form.next()
    await message.reply("Добавьте свое фото")


@dp.message_handler(lambda message: not message.photo, state=Form.user_photo)
async def process_photo_invalid(message: types.Message):
    """
    Если пользователь не загружает фото
    """
    return await message.reply("Фотография не найдена в сообщении =(\nЗагрузи свою фотку")


@dp.message_handler(content_types=['photo'], state=Form.user_photo)
async def process_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        document_id = message.photo[-1].file_id
        file_info = await bot.get_file(document_id)
        path = f'http://api.telegram.org/file/bot{API_TOKEN}/{file_info.file_path}'
        data['user_photo'] = path

    await Form.next()
    await message.reply("Сколько тебе лет?")


# Check age. Age gotta be digit
@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.age)
async def process_age_invalid(message: types.Message):
    """
    Если возраст неверный
    """
    return await message.reply("Возраст должен быть числом.\nСколько тебе лет? (только цифры)")


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.age)
async def process_age(message: types.Message, state: FSMContext):
    # Update state and data
    await Form.next()
    await state.update_data(age=int(message.text))

    # Configure ReplyKeyboardMarkup
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Мужчина", "Женщина")
    markup.add("Другие")

    await message.reply("Какого Вы пола?", reply_markup=markup)


@dp.message_handler(lambda message: message.text not in ["Мужчина", "Женщина", "Другие"], state=Form.gender)
async def process_gender_invalid(message: types.Message):
    """
    В этом примере пол должен быть одним из: Мужской, Женский, Другой.
    """
    return await message.reply("Плохое гендерное имя. Выберите свой пол с клавиатуры.")


@dp.message_handler(state=Form.gender)
async def process_gender(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['gender'] = message.text

        # Remove keyboard
        markup = types.ReplyKeyboardRemove()

        # And send message
        await bot.send_message(
            message.chat.id,
            md.text(
                md.text('Привет! Рад встрече,', md.bold(data['name'])),
                md.text('Возраст:', md.code(data['age'])),
                md.text('Пол:', data['gender']),
                sep='\n',
            ),
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN,
        )

    # Finish conversation
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

