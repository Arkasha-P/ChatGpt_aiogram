from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types


class FSMstates(StatesGroup):
    personalities = State()

@dp.message_handler(commands=['Добавить_персону'], state=None)
async def add_persona(message: types.Message):
    await FSMstates.personalities.set()
    await message.reply("Добавте вашему боту персону. До 150 символов")

@dp.message_handler(state=FSMstates.personalities)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['personalities'] = message.text

        db.set_personalities(message.chat.id, message.text)

        await bot.send_message(
            message.chat.id,
             "Персона сохранена"
        )
        await state.finish()