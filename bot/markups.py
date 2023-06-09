from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

btnSub = KeyboardButton('Подписка')
btnProfile = KeyboardButton('Профиль')
btnSetting = KeyboardButton('Настройки')

btnPersonalities = KeyboardButton('Персона')
btnPersonalities_add = KeyboardButton('/Добавить_персону')
btnPersonalities_reset = KeyboardButton('/Сбросить_персону')

#=============== free menu ===================
freeMenu = ReplyKeyboardMarkup(resize_keyboard= True)
freeMenu.add(btnSetting, btnSub)  # клавиатура над клавиатурой фрии

settingMenu = ReplyKeyboardMarkup(resize_keyboard= True).add(btnProfile, btnPersonalities)

#=============== sub menu ====================
premiumMenu = ReplyKeyboardMarkup(resize_keyboard= True)
premiumMenu.add(btnSetting)  # добавление

settingMenu = ReplyKeyboardMarkup(resize_keyboard= True).add(btnProfile, btnPersonalities)

PersonalitiesMenu = ReplyKeyboardMarkup(resize_keyboard= True).add(btnPersonalities_add, btnPersonalities_reset)


#=============== subbutton ===================
sub_inline_markup = InlineKeyboardMarkup(row_width=1)
btnSubMonth = InlineKeyboardButton(text="Месяц - 300 рублей", callback_data="submonth")
sub_inline_markup.insert(btnSubMonth) # кнопка под сообщениями купить 



