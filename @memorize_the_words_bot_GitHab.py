import logging
import asyncio
import random
from time import time
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

BOT_TOKEN = 'your token'

loop = asyncio.new_event_loop()
logging.basicConfig(level=logging.INFO)
bot = Bot(BOT_TOKEN, parse_mode='HTML')
storage = MemoryStorage()
dp = Dispatcher(bot, loop=loop, storage=storage)

keyboards = InlineKeyboardMarkup(row_width=1, inline_keyboard=[
    [
        InlineKeyboardButton(text='Начать игру', callback_data='play')
    ],
])


class Game(StatesGroup):
    level_1 = State()


def range_words():
    list_words = []  # извлекаем все слова с этот список
    with open('list_words.txt', encoding='utf8') as lw:
        for i in lw:
            list_words.append(i.replace('\n', ''))
    temporary_list = []  # создаем временный список для хранения 30 слов
    while len(temporary_list) != 30:
        temporary_list = random.sample(list_words, 30)
        temporary_list = list(set(temporary_list))  # используем множества для уникальности слов
    temporary_list = sorted(temporary_list)  # сортируем список по алфавиту
    string_words = '        '.join(temporary_list)  # создаем строку
    return string_words


@dp.message_handler(commands=['start'])
async def get_start(message: Message):
    await message.answer('<b>Приветствую!</b> <i>Я бот, который помогает прокачивать оперативную (краткосрочную) '
                         'память. Я дам тебе список из 30 слов, которые нужно запомнить.</i> <b>Через две минуты</b><i>'
                         ' я удалю список и тебе будет предложено вспомнить слова. Отправляй мне по одному слову, '
                         'и я буду отвечать, было ли оно в списке или нет. Твоя задача, вспомнить все слова. Удачи, '
                         'мой друг!</i>',
                         parse_mode='HTML', reply_markup=keyboards)


@dp.callback_query_handler(text='play', state=None)
async def play_game(call: CallbackQuery):
    await call.answer(text=f'Запомни все слова!', show_alert=True)
    string_words = range_words()
    print(string_words, '\n\n')
    del_mes = await bot.send_message(call.from_user.id, text=f'{string_words}')
    await asyncio.sleep(120)
    await del_mes.delete()
    await bot.send_message(call.from_user.id, text='Вспомни слова и отправляй мне их по одному!\n'
                                                   'Чтобы завершить игру, в МЕНЮ есть кнопка ОТМЕНА!')
    s = set()
    await Game.level_1.set()

    @dp.message_handler(state="*", commands='cancel')
    @dp.message_handler(Text(equals='отмена', ignore_case=True), state="*")
    async def cancel_handler(message: Message, state: FSMContext):
        current_state = await state.get_state()
        if current_state is None:
            return
        await state.finish()
        await message.reply('Игра окончена!')

    @dp.message_handler(state=Game.level_1)
    async def level_1(message: Message, state: FSMContext):
        async with state.proxy() as data:
            data['word'] = message.text.lower().replace(' ', '').replace('ё', 'е')
        list_words = string_words.split()
        if data['word'] in list_words:
            s.add(data['word'])
            await bot.send_message(message.from_user.id, text=f'Верно указанных слов: {len(s)}')
        else:
            await bot.send_message(message.from_user.id, text=f'Не было такого слова, не выдумывай!')
        if len(s) == 30:
            await bot.send_message(message.from_user.id, text=f'Поздравляю, у тебя отличная память! 🥳')
            await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
