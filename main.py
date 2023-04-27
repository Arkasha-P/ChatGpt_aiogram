import logging
import time
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.message import ContentType
from aiogram.types import ChatActions

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from aiogram.contrib.fsm_storage.memory import MemoryStorage

import openai

import bot.markups as nav
from bot.cfg import *
from bot.db import Database

import datetime

# Set up the bot and OpenAI API credentials 
bot_token = TELEGRAM_BOT_TOKEN
api_key = OPENAI_API_KEY

log = "data/log"
logging.basicConfig(filename=log, filemode='a', level=logging.INFO)

#logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()

bot = Bot(token=bot_token)
dp = Dispatcher(bot, storage=storage)
db = Database(DATABASE)

MAX_TOKEN = 0

openai.api_key = api_key

def days_to_seconds(days):
     return days * 24 * 60 *  60

def time_sub_day(get_time):
     time_now = int(time.time())
     middle_time = int(get_time) - time_now

     if middle_time <= 0:
          return False
     else:
          dt = str(datetime.timedelta(seconds=middle_time))
          dt = dt.replace("days", "дней")
          dt = dt.replace("day", "день")
     return dt



messages = {}



@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
     try:
          await dp.bot.set_my_commands([
          types.BotCommand("start", "Запустить бота"),
          types.BotCommand("help", "Помощь"),
          types.BotCommand("newtopic", "Сбросить диалог"),
          # types.BotCommand("add_personal", "Добавте вашему боту персону. До 150 символов"),
          # types.BotCommand("Сбросить_персону", "Сбросить персону"),
          ]) 
          

          if(not db.user_exists(message.from_user.id)): # проверка на наличия пользователя в базе  если пользователя нет в базе то он автоматически добавляется
               db.add_user(message.from_user.id) # команда добавления пользователя в базу (Добавляет user_id)
               db.set_nickname(message.from_user.id, message.from_user.username) # Добавляет username login
               db.set_personalities(message.from_user.id, "Вы ассистент, готовы помочь")
               await bot.send_message(message.from_user.id, "Добро пожаловать! Я - ваш бот-ассистент, созданный на основе инновационных технологий искусственного интеллекта ChatGPT. 🤖Я могу предоставить вам различную информацию, помочь решать задачи и делать жизнь проще. Также вы можете задать мне персону и я буду давать ответы в рамках своего персонажа💡. Будет почетом мне помочь вам! 👍", reply_markup=nav.freeMenu)
               await bot.send_message(message.from_user.id, "Уважаемый пользователь! Мы рады предоставить Вам нашу бесплатную версию сервиса, где вы сможете вводить тексты до 150 символов, а также получать ответы со сложностью, не превышающей 1500 токенов. 😊 Для получения большего функционала мы предлагаем ежемесячную подписку, которая позволит Вам в полной мере воспользоваться всеми доступными возможностями нашего сервиса. 💡 Спасибо за Ваш выбор! 👍", reply_markup=nav.freeMenu)
          else:
               
               await bot.send_message(message.from_user.id, "Приветствую🤖\r\n\r\nМы рады сообщить, что Ваш 🤖 бот успешно активирован.", reply_markup=nav.freeMenu)
               username = message.from_user.username
               messages[username] = []
     except Exception as e:
          logging.error(f'Error in start_cmd: {e}')

@dp.message_handler(commands=['help'])
async def help_cmd(message: types.Message) -> None:
          await bot.send_message(message.from_user.id, HELP_DESCRIPTION)




@dp.message_handler(commands=['newtopic'])
async def new_topic_cmd(message: types.Message):
    try:
        userid = message.from_user.id
        messages[str(userid)] = []
        await message.reply('Starting a new topic! * * * \n\nНачинаем новую тему! * * *', parse_mode='Markdown')
    except Exception as e:
        logging.error(f'Error in new_topic_cmd: {e}')


@dp.message_handler(commands=['Сбросить_персону'])
async def new_topic_cmd(message: types.Message):
    try:
        db.set_personalities(message.from_user.id, "Вы ассистент, готовы помочь")
        await message.reply('Персона сброшена', parse_mode='Markdown',reply_markup=nav.premiumMenu)
    except Exception as e:
        logging.error(f'Error in new_topic_cmd: {e}')

# =========================== add persona
class FSMstates(StatesGroup):
     personalities = State()

@dp.message_handler(commands=['Добавить_персону'], state=None)
async def add_persona(message: types.Message):
     if db.get_sub_status(message.from_user.id) == False: # тоесть статус free 
          await bot.send_message(message.from_user.id,"Для изменения параметров персонажа необходимо иметь подписку. \r\nНастройка персонажа позволяет присвоить Вашему боту-ассистенту роль пирата, космодесантника или юриста, все ограничивается в вашу фантазию и 150 символов вводимого текста для персоны.", reply_markup=nav.freeMenu)
          return
     else:
          await FSMstates.personalities.set()
          await message.reply("Добавте вашему боту персону. До 150 символов")

@dp.message_handler(state=FSMstates.personalities)
async def process_name(message: types.Message, state: FSMContext):
     
     if len(message.text) >= 150: 
          await bot.send_message(
          chat_id=message.from_user.id,
          text=f'"К сожалению, Вы ввели слишком много символов (более 150)."',
          )
          return
     
     async with state.proxy() as data:
          data['personalities'] = message.text

          db.set_personalities(message.chat.id, message.text)

          await message.reply("Персона сохранена",
          parse_mode='Markdown',
          reply_markup=nav.premiumMenu)
     await state.finish()

# =========================== end


@dp.message_handler()
async def echo_msg(message: types.Message):
     
     try:
          user_message = message.text
          userid = message.from_user.username

          if message.chat.type == 'private': # проверяет является чат в личным а не публичным (например общение через групповой чат)
               user_sub = time_sub_day(db.get_time_sub(message.from_user.id))

          # при каждом вводимом сообщении проверяет пользователя на наличие подписки через функцию таймера он проверяет реальное время
          if db.get_sub_status(message.from_user.id) == True:  
               db.set_signup(message.from_user.id, "sub")
          elif db.get_sub_status(message.from_user.id) == False:
               db.set_signup(message.from_user.id, "free")
               db.set_time_sub(message.from_user.id, 0)
               db.set_personalities(message.from_user.id, "Вы ассистент, готовы помочь")

          if message.text == 'Настройки':
               await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
               await bot.send_message(message.from_user.id, "Настройки",reply_markup=nav.settingMenu)
               return

          if message.text == 'Персона':
               await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
               if db.get_sub_status(message.from_user.id) == False:
                    await bot.send_message(message.from_user.id, "Для изменения параметров персонажа необходимо иметь подписку. \r\nНастройка персонажа позволяет присвоить Вашему боту-ассистенту роль пирата, космодесантника или юриста, все ограничивается в вашу фантазию и 150 символов вводимого текста для персоны.", reply_markup=nav.freeMenu)
               else:
                    await bot.send_message(message.from_user.id, "Вы можете использовать функцию \"Персона\" для задания определенного имени, роли или характера вашему боту-ассистенту. Это позволит наделить вашего бота более индивидуальным и уникальным стилем и поведением, что поможет улучшить взаимодействие с пользователями.", reply_markup=nav.PersonalitiesMenu)
               return

          if message.text == 'Профиль': # реакция на команду профиль

               await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
               user_nickname = "Ваш ник: " + db.get_nickname(message.from_user.id)
               
               if user_sub == False:
                    user_sub = "Free"
               user_sub = "\nПодписка: " + user_sub

               await bot.send_message(message.from_user.id, user_nickname + user_sub)
               PERSONALITIES = db.get_personalities(message.from_user.id)
               
               
               if db.get_sub_status(message.from_user.id) == True:
                    await bot.send_message(message.from_user.id, "Персона вашего бота:\n\n\""+PERSONALITIES+"\"",reply_markup=nav.premiumMenu)
               else:
                    await bot.send_message(message.from_user.id, "Персона вашего бота:\n\n\""+PERSONALITIES+"\"",reply_markup=nav.freeMenu)
               return

          elif message.text == 'Подписка':# реакция на команду подписка
               if db.get_signup(message.from_user.id) == "sub":
                    await bot.send_message(message.from_user.id, "У вас уже есть 🌟 премиум подписка", reply_markup=nav.premiumMenu)
                    logging.info(f'{userid}: {user_message}')
                    return
               else:
                    await bot.send_message(message.from_user.id, description, reply_markup=nav.sub_inline_markup)
                    logging.info(f'{userid}: {user_message}')
                    return

          else: # все остальные команды 
               await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
               if db.get_signup(message.from_user.id) == "sub": # здесь все остальные команды при подписке
                    #await bot.send_message(message.from_user.id, "Что? 110", reply_markup=nav.premiumMenu) # если при нажатии на старт пользователь уже в базе то выдаётся сообщение 
                    MAX_TOKEN = MAX_TOKEN_SUB
                    logging.info(f'{userid}: {user_message}')
                    
               else: # здесь все остальные команды при отсутствии подписки
                    MAX_TOKEN = MAX_TOKEN_FREE
                    if len(message.text) >= 150: 
                         await bot.send_message(
                         chat_id=message.from_user.id,
                         text=f'"К сожалению, Вы ввели слишком много символов (более 150). Следующее ограничение можно снять, используя подписку. \r\n\r\nСпасибо, что выбрали наш сервис для оптимизации процессов. 🔍"',
                         reply_markup = nav.sub_inline_markup
                         )
                         logging.info(f'{userid}: {user_message}')
                         return

     # Add the user's message to their message history

          PERSONALITIES = db.get_personalities(message.from_user.id)
          if userid not in messages:
               messages[userid] = []
          messages[userid].append({"role": "user", "content": user_message})
          messages[userid].append({"role": "system", "content": PERSONALITIES})
          messages[userid].append({"role": "user",
                                 "content": f"chat: {message.chat} Сейчас {time.strftime('%d/%m/%Y %H:%M:%S')} user: {message.from_user.first_name} message: {message.text}"})
          

        # Check if the message is a reply to the bot's message or a new message
          should_respond = not message.reply_to_message or message.reply_to_message.from_user.id == bot.id

          if should_respond:
            # Отправьте сообщение "обработка", чтобы указать, что бот работает
               processing_message = await message.reply(
               'I need to think 🤔 \n(If the bot does not respond, write /newtopic) * * * \n\nМне нужно подумать 🤔 \n(Если бот не отвечает, напишите /newtopic) * * *',
               parse_mode='Markdown')

               # Send a "typing" action to indicate that the bot is typing a response
               await bot.send_chat_action(chat_id=message.chat.id, action="typing")

               # Generate a response using OpenAI's Chat API
               completion = await openai.ChatCompletion.acreate(
                    model="gpt-3.5-turbo",
                    messages=messages[userid],
                    max_tokens=MAX_TOKEN,
                    temperature=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                    user=userid
               )
               chatgpt_response = completion.choices[0]['message']

               #await bot.send_message(message.from_user.id, "Это 175 строка")

               await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
               # Add the bot's response to the user's message history
               messages[userid].append({"role": "assistant", "content": chatgpt_response['content']})
               logging.info(f'ChatGPT response: {chatgpt_response["content"]}')
               #await bot.send_message(message.from_user.id, "Это 179 строка")
               await bot.send_chat_action(message.chat.id, ChatActions.TYPING)
               # Отправить ответ бота пользователю

               # Delete the "processing" message
               await bot.delete_message(chat_id=processing_message.chat.id, message_id=processing_message.message_id)

               if (ALIVE_TEXT == False):
                    await message.reply(chatgpt_response['content'])
               #await bot.send_message(message.from_user.id, "Это 184 строка")
               else:
                    random_number = 20                   #random.randint(5, 25)
                    text = chatgpt_response['content']
                    msg = await bot.send_message(message.chat.id, '_')
                    tbp = text[:random_number]
                    for x in range(0, len(text), random_number):
                         await bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=f'{tbp}_')
                         #random_number = random.randint(5, 25)
                         tbp = text[0:x+random_number]
                         time.sleep(RESPONSE_TIME)
                         await bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=tbp)
               await bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=text)
                    



     except Exception as ex:
        # Если возникает ошибка, попробуйте начать новую тему
          if ex == "context_length_exceeded":
            await message.reply(
                'The bot ran out of memory, re-creating the dialogue * * * \n\nУ бота закончилась память, пересоздаю диалог * * *',
                parse_mode='Markdown')
            await new_topic_cmd(message)
            await echo_msg(message)



@dp.callback_query_handler(text="submonth") # обработчик кторый выводит информацию о подписке
async def submonth(call: types.CallbackQuery):
     await bot.delete_message(call.from_user.id, call.message.message_id)
     await bot.send_invoice(chat_id=call.from_user.id, title="Подписка ⚜️", description=description, payload="month_sub", provider_token=YOOTOKEN, currency="RUB", start_parameter="test", prices=[{"label": "Руб", "amount": 15000}])

@dp.pre_checkout_query_handler() #проверяет что товар есть на складе и возвращает ок
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
     await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message_handler(content_types = ContentType.SUCCESSFUL_PAYMENT) #проверяет что оплата прошла вслучае если всё хорошо то информирует пользователя что оплата прошла и присваевает ему время и статус
async def process_pay(message: types.Message):
     if message.successful_payment.invoice_payload == "month_sub":
            time_sub = int(time.time()) + days_to_seconds(30)
            db.set_time_sub(message.from_user.id, time_sub)
            db.set_signup(message.from_user.id, "sub")
            await bot.send_message(message.from_user.id, "Вам выдана ⚜️ подписка", reply_markup=nav.premiumMenu)


if __name__ == '__main__':
    executor.start_polling(dp)
