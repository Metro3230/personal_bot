import chat_processing as chat
import openAI_req as openAI
from pathlib import Path
from dotenv import load_dotenv
import os
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import telegramify_markdown #библитека преобразования markdown в телеграммный markdown_n2
from datetime import datetime
import logging
import asyncio
import shutil
import configparser


script_dir = Path(__file__).parent  # Определяем путь к текущему скрипту
data_dir = script_dir / 'data'
msg_hist_dir = data_dir / 'msg_hits'   #папка с историями сообщений
log_file = data_dir / 'log.log'
env_file = data_dir / '.env'
data_zip = script_dir / 'data.zip'
config_file = data_dir / 'config.ini'

config = configparser.ConfigParser()  # настраиваем и читаем файл конфига
config.read(config_file)

load_dotenv(env_file)
tg_token = os.getenv('TG_TOKEN')    # читаем token ai c .env

bot = AsyncTeleBot(tg_token)
# async_bot = AsyncTeleBot(tg_token)


#  логгер для моего скрипта
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  #  уровень логов для моего скрипта

#  обработчик для записи в файл
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)  # Уровень для файлового обработчика
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

#  логгер для сторонних библиотек
logging.getLogger().setLevel(logging.WARNING)

temp_spam_text = None

async def login(chat_id, message, sender_name): #----ЛОГИН--------------------------------------+
    try:
        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль
            await bot.send_message(chat_id, "Ошибка: формат команды /login пароль")
            return
        
        input_password = command_parts[1]

        if input_password == os.getenv('LOGIN_PASS'):        # Проверяем правильность пароля
            chat.set_proc_flag(chat_id, 1, sender_name)            
            logger.info('пользователь ' + str(chat_id) + ' залогинился')
            text = ("Добро пожаловать в личный ИИ бот\.\n" +
                    "Не забывай использовать команды управления ботом\. Важно помнить\, что каждый раз " +
                    "начиная общение на новую тему \- нужно нажимать \"**начать новую тему**\"" +
                    "\, иначе ответы будут не совсем релевантны и общение выйдет в копеечку\.")
            await bot.send_message(chat_id, text, parse_mode='MarkdownV2')
        else:
            await bot.send_message(chat_id, "Неверный пароль.")

    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}")
        logger.error(f"Ошибка логининга - {e}")
        
        

async def handle_dw_data(chat_id, message): #---скачивание данных-------------------------------------+
    try:
        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль
            await bot.send_message(chat_id, "Ошибка: формат команды /dw_data пароль")
            return
        
        input_password = command_parts[1]

        if input_password == os.getenv('SERVICE_PASS'):        # Проверяем правильность пароля
            shutil.make_archive(str(data_zip).replace('.zip', ''), 'zip', data_dir)
            with open(data_zip, 'rb') as file:
                await bot.send_document(chat_id, file)
            os.remove(data_zip)
            logger.info('data скачен пользователем ' + str(chat_id))
        else:
            await bot.send_message(chat_id, "Неверный пароль.")

    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}")
        logger.error(f"Ошибка скачивания данных - {e}")
        

async def handle_dw_config(chat_id, message): #---скачивание конфига-------------------------------------+
    try:
        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль
            await bot.send_message(chat_id, "Ошибка: формат команды /dw_config пароль")
            return
        
        input_password = command_parts[1]

        if input_password == os.getenv('SERVICE_PASS'):        # Проверяем правильность пароля
            with open(config_file, 'rb') as file:
                await bot.send_document(chat_id, file)
            await bot.send_message(chat_id, 'Измени файл и закинь обратно в этот чат с командой `/set_config пароль` в подписи к отправляемому файлу', parse_mode='MarkdownV2')
            logger.info('config скачен пользователем ' + str(chat_id))
        else:
            await bot.send_message(chat_id, "Неверный пароль.")

    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}")
        logger.error(f"Ошибка скачивания данных - {e}")
        

async def handle_set_config(chat_id, message, file_id, file_name): #---обновление конфига-------------------------------------+
    try:
        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 2:         # Проверяем, что есть и пароль
            await bot.send_message(chat_id, "Ошибка: формат команды /set_config пароль")
            return
        
        input_password = command_parts[1]

        if input_password == os.getenv('SERVICE_PASS') and file_name == 'config.ini':        # Проверяем правильность пароля
            file_path = (await bot.get_file(file_id)).file_path
            downloaded_file = await bot.download_file(file_path)
            with open(config_file, 'wb') as new_file:            # Сохраняем файл на сервере, заменяя старый
                new_file.write(downloaded_file)
            await bot.send_message(chat_id, "Файл настроек успешно обновлён, надеюсь он адекватный и Вы ничего не сломали")
            logger.info('config.ini заменён пользователем ' + str(chat_id))
        else:
            await bot.send_message(chat_id, "Либо файл называется не *config\.ini*\, либо пароль не верен\. Используй `/set_config пароль` как описание при отправке файла *config\.ini*", parse_mode='MarkdownV2')

    except Exception as e:
        await bot.send_message(chat_id, f"Произошла ошибка: {e}")
        logger.error(f"Ошибка скачивания данных - {e}")
        
        

async def handle_new_service_pass(chat_id, message): #----------обновление сервисного пароля--------------+
    try:
        old_service_pass = os.getenv('SERVICE_PASS')       # пишем в лог старый файл на всякий
        logger.info('попытка смены сервисного пароля: "' + old_service_pass + '" на новый...')

        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 3:         # Проверяем, что есть и пароль, и новый пароль
            await bot.send_message(chat_id, "Ошибка: формат команды /new_service_pass сервисный_пароль новый_сервисный_пароль")
            return
        
        input_password = command_parts[1]
        new_service_pass = command_parts[2]

        if input_password == os.getenv('SERVICE_PASS'):        # Проверяем правильность старого сервисного пароля
            update_env_variable('SERVICE_PASS', new_service_pass)
            await bot.send_message(chat_id, "Сервисный пароль успешно обновлён!")
            logger.info('новый сервсиный пароль установлен: ' + new_service_pass)
        elif input_password == os.getenv('LOGIN_PASS'):  #если это пароль на логин
            await bot.send_message(chat_id, "Это пароль для входа. Так не прокатит.")
            logger.info('Входной пароль не обновлён пользователем ' + str(chat_id) + '(ввёл пароль на подписку)')
        else:
            await bot.send_message(chat_id, "Неверный пароль.")

    except Exception as e:
        logger.error(f"Произошла ошибка обновления сервисного пароля - {e}")
        await bot.send_message(chat_id, f"Произошла ошибка: {e}")


async def handle_new_login_pass(chat_id, message): #----------обновление входного пароля--------------+
    try:
        old_login_pass = os.getenv('LOGIN_PASS')       # пишем в лог старый на всякий
        logger.info('попытка смены сервисного пароля: "' + old_login_pass + '" на новый...')

        command_parts = message.split(maxsplit=2)         # Разделяем текст команды на части

        if len(command_parts) < 3:         # Проверяем, что есть и пароль, и новый пароль
            await bot.send_message(chat_id, "Ошибка: формат команды /new_login_pass сервисный_пароль новый_входной_пароль")
            return
        
        input_password = command_parts[1]
        new_login_pass = command_parts[2]

        if input_password == os.getenv('SERVICE_PASS'):        # Проверяем правильность сервисного пароля
            update_env_variable('LOGIN_PASS', new_login_pass)
            await bot.send_message(chat_id, "Входной пароль успешно обновлён!")
            logger.info('новый входной пароль установлен: ' + new_login_pass)
        elif input_password == os.getenv('LOGIN_PASS'):  #если это пароль на логин
            await bot.send_message(chat_id, "Это пароль для входа. Так не прокатит.")
            logger.info('Входной пароль не обновлён пользователем ' + str(chat_id) + '(ввёл пароль на подписку)')
        else:
            await bot.send_message(chat_id, "Неверный пароль.")

    except Exception as e:
        logger.error(f"Произошла ошибка обновления входного пароля - {e}")
        await bot.send_message(chat_id, f"Произошла ошибка: {e}")



def update_env_variable(key, value): #---функция обновления параметра в файле secrets.env-----------+

    if os.path.exists(env_file):    # Считаем текущие данные из .env файла
        with open(env_file, 'r') as file:
            lines = file.readlines()
    else:
        lines = []

    key_found = False    # Флаг, чтобы понять, был ли ключ найден
    new_lines = []

    for line in lines:    # Проходим по каждой строке и ищем ключ
        if line.startswith(f'{key}='):        # Если строка начинается с нужного ключа, заменяем его
            new_lines.append(f'{key}={value}\n')
            key_found = True
        else:
            new_lines.append(line)

    if not key_found:    # Если ключ не найден, добавляем его в конец
        new_lines.append(f'{key}={value}\n')

    with open(env_file, 'w') as file:    # Записываем обновленные данные обратно в .env файл
        file.writelines(new_lines)
    
    load_dotenv(env_file, override=True)    # повторно загружаем значения из env с перезаписью


#------------------------------------------отправка сообщения (с проверкой на длину)-----------------------

async def send_msg(chat_id, message_text):
    try:
        message_text = telegramify_markdown.markdownify(message_text)      # чистим markdown
        max_msg_length = config['mainconf']['max_msg_length']
        text_lines = message_text.split('\n')
        current_message = ''
        for line in text_lines:
            if len(current_message) + len(line) + 1 > int(max_msg_length):
                await bot.send_message(chat_id, current_message, parse_mode='MarkdownV2', reply_markup=types.ReplyKeyboardRemove())
                current_message = line
            else:
                if current_message:
                    current_message += '\n' + line
                else:
                    current_message = line
        if current_message:
            await bot.send_message(chat_id, current_message, parse_mode='MarkdownV2', reply_markup=types.ReplyKeyboardRemove())   
    except Exception as e:
        await bot.send_message(chat_id, f"Ошибка - {e}")   
        logger.error(f"Ошибка стандартной обработки стандартного вопроса - {e}")
        
#----------------------------------------------------------------------------------------------------------


#----------------------------------------стандартная обработка стандартного вопроса------------------------


async def question_for_ai(chat_id, username, message_text):
    wait_message_sent = False
    wait_message_id = None
    typing_task = None
    wait_message_task = None

    try:
        
        # отправлчяем статус "набирает сообщение" каждые Х секунд
        async def send_typing_periodically(): 
            while True:
                try:
                    await bot.send_chat_action(chat_id, 'typing', timeout=10)
                    await asyncio.sleep(7)
                except Exception as e:
                    logger.error(f"send_chat_action не отправлен (для chat_id {chat_id}) -- {e}")
                    break
                                
        # задача для отправки успокаивающего сообщения через Х секунд после начала ожидания ответа от API ИИ
        async def send_wait_message():
            nonlocal wait_message_sent, wait_message_id
            await asyncio.sleep(int(config['mainconf']['a_calming_message_delay']))
            text = telegramify_markdown.markdownify(config['mainconf']['a_calming_message'])      # чистим markdown
            msg = await bot.send_message(chat_id, text, parse_mode='MarkdownV2', reply_markup=types.ReplyKeyboardRemove())
            wait_message_sent = True
            wait_message_id = msg.message_id

        # Запускаем задачи /\
        typing_task = asyncio.create_task(send_typing_periodically())
        wait_message_task = asyncio.create_task(send_wait_message())

        chat.save_message_to_json(chat_id=chat_id, role="user", sender_name=username, message=message_text)   #записываем текст сообщения от ЮЗЕРА в историю сообщений

        last_messages = chat.get_context(chat_id)
        lang_model = chat.proc_lang_model(chat_id)
        
        openai_models = []
        openai_models.append(config['mainconf']['btn_text_1'])
        openai_models.append(config['mainconf']['btn_text_2'])
        openai_models.append(config['mainconf']['btn_text_3'])
        openai_models.append(config['mainconf']['btn_text_4'])
        openai_models.append(config['mainconf']['btn_text_5'])
        
        deepseek_models = []
        deepseek_models.append(config['mainconf']['btn_text_6'])
        deepseek_models.append(config['mainconf']['btn_text_7'])
        
        if lang_model in openai_models:        # запрос в зависимости от модели
            response_text, price, response_req_tokens = await openAI.req_to_openai(last_messages, lang_model)   #отправляем историю чата (чат ид) боту
        elif lang_model in deepseek_models:
            response_text, price, response_req_tokens = await openAI.req_to_deepseek(last_messages, lang_model)   #отправляем историю чата (чат ид) боту
                
        
        # Отменяем задачу отправки сообщения "Нужно ещё подождать", если она еще не выполнена
        wait_message_task.cancel()
        try:
            await wait_message_task
        except asyncio.CancelledError:
            pass  # Ожидаем завершения задачи, игнорируем ошибку отмены
        
        await send_msg(chat_id, response_text)        # отправляем ответ ии пользователю
        
        chat.save_message_to_json(chat_id=chat_id, role="assistant", sender_name=username, message=response_text, price=price)      #записываем текст сообщения от БОТА в историю сообщений

    except Exception as e:
        logger.error(f"Ошибка при обработке запроса к ИИ от {chat_id} - {e}")
        text = telegramify_markdown.markdownify(config['mainconf']['msg_if_req_error'])      # чистим markdown
        await bot.send_message(chat_id, text, parse_mode='MarkdownV2', reply_markup=types.ReplyKeyboardRemove()) # предупреждаем пользователя об ощибке
        
    finally:
        # Если сообщение "нужно подождать" было отправлено, удаляем его
        if wait_message_sent:
            try:
                await bot.delete_message(chat_id, wait_message_id)
            except Exception as e:
                logger.error(f"Не удалось удалить сообщение: {e}")

        # Останавливаем задачу отправки 'typing'
        if typing_task:
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass  # Ожидаем завершения задачи, игнорируем ошибку отмены

#----------------------------------------------------------------------------------------------------------


# -----------------------------------Основной обработчик всех сообщений------------------------------------

@bot.message_handler(content_types=['text', 'photo', 'document', 'video', 'voice', 'audio', 'contact', 'location', 'sticker', 'animation'])
async def handle_message(message):
    
    content_type = message.content_type
    message_text = message.text if message.text is not None else message.caption #текст или описание = текст
    chat_id = message.chat.id
    username = message.from_user.username
    message_id = message.message_id
    caption=message.caption
    proc_flag = chat.get_proc_flag(chat_id)
    

    if (message_text):   
        if message_text.startswith('/login'):
            await login(chat_id, message_text, username)
        elif proc_flag == 0:
            await bot.send_message(chat_id, "Что-бы начать пользоваться, введи `/login пароль`. Пароль скажет Саня.")                  # Отправка сообщение с ссылкой  
        else:
            if message_text.startswith('/'): #обработка сервисных команд----+-+        
                if message_text == "/service" or message_text == "/admin":
                    text = ('`/dw_data сервисный_пароль` - скачать папку с данными\n' +
                            '`/dw_config сервисный_пароль` - скачать текущий файл настроек\n' +
                            '`/new_service_pass старый_сервисный_пароль новый_сервисный_пароль` - замена сервисного пароля\n' +
                            '`/new_login_pass сервисный_пароль новый_входной_пароль` - замена входного пароля\n')
                    text = telegramify_markdown.markdownify(text)      # чистим markdown
                    await bot.send_message(chat_id, text, parse_mode='MarkdownV2')
                                    
                elif message_text.startswith('/get_stat'): #+++++++++++++    
                    total_cost, language_model, role = chat.get_stat(chat_id)
                    total_cost = round(total_cost, 2)
                    currency_symbol = config['mainconf']['currency_symbol']
                    if role == None:
                        role = "Стандарт"
                    balance = await openAI.get_balance() 
                    text = (f"`Всего потрачено саниных денег: {total_cost} {currency_symbol}`\n" +
                            f"`Баланс ProxyAPI: {balance}`\n" +  
                            f"`Языковая модель: {language_model}`\n" +
                            f"`Роль ассистента: {role}`\n" )
                    await bot.send_message(chat_id, text, parse_mode='MarkdownV2')                                 
                    
                elif message_text.startswith('/dw_data'):
                    await handle_dw_data(chat_id, message_text)                     
                    
                elif message_text.startswith('/new_service_pass'):
                    await handle_new_service_pass(chat_id, message_text)         
                    
                elif message_text.startswith('/new_login_pass'):
                    await handle_new_login_pass(chat_id, message_text)
                                    
                elif message_text.startswith('/dw_config'):
                    await handle_dw_config(chat_id, message_text)
                    
                elif message_text.startswith('/set_config'):
                    await handle_set_config(chat_id, message_text, message.document.file_id, message.document.file_name)

                elif message_text.startswith('/remove_context'): #++++++++
                    chat.remove_context(chat_id)
                    await bot.send_message(chat_id, "История сообщений удалена из памяти бота, начни новую тему:")
                
                elif message_text.startswith('/new_assistent_role'): #++++++++
                    chat.set_proc_flag(chat_id, 2, username)
                    text = "Следующим сообщением отправь новую роль твоего ассистента:"                    
                    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)    # Создаем объект клавиатуры
                    keyboard.row("отмена", "очистить")
                    await bot.send_message(chat_id, text, reply_markup=keyboard)       # Отправляем сообщение с клавиатурой
                    
                elif message_text.startswith('/new_lang_model'): #++++++++
                    chat.set_proc_flag(chat_id, 3, username)                    
                    model_arr = []
                    model_arr.append(config['mainconf']['btn_text_1'])
                    model_arr.append(config['mainconf']['btn_text_2'])
                    model_arr.append(config['mainconf']['btn_text_3'])
                    model_arr.append(config['mainconf']['btn_text_4'])
                    model_arr.append(config['mainconf']['btn_text_5'])
                    model_arr.append(config['mainconf']['btn_text_6'])
                    model_arr.append(config['mainconf']['btn_text_7'])
                    
                    currency_symbol = config['mainconf']['currency_symbol']
                    
                    text = ""
                    text += config['mainconf']['about']
                    text += "\n\n\n\n"  
                    text += "Цены  ( запрос / ответ ):\n"                    
                    for item in model_arr:
                        text += item + "   ( " + config['AIconf'][f'price_{item}_req'] + currency_symbol + " / " + config['AIconf'][f'price_{item}_resp'] + currency_symbol + " )" + "\n"   
                    text += "\nВыбери новую языковую модель:\n"               
                    
                    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)    # Создаем объект клавиатуры
                    markup_1 = types.KeyboardButton(config['mainconf']['btn_text_1'])     # Добавляем кнопки
                    markup_2 = types.KeyboardButton(config['mainconf']['btn_text_2'])
                    markup_3 = types.KeyboardButton(config['mainconf']['btn_text_3'])
                    markup_4 = types.KeyboardButton(config['mainconf']['btn_text_4'])
                    markup_5 = types.KeyboardButton(config['mainconf']['btn_text_5'])
                    markup_6 = types.KeyboardButton(config['mainconf']['btn_text_6'])
                    markup_7 = types.KeyboardButton(config['mainconf']['btn_text_7'])
                    
                    keyboard.row(markup_1, markup_2)     
                    keyboard.row(markup_3, markup_4)
                    keyboard.row(markup_5, markup_6)
                    keyboard.row(markup_7, "отмена")
                    text = telegramify_markdown.markdownify(text)      # чистим markdown
                    await bot.send_message(chat_id, text, reply_markup=keyboard, parse_mode='MarkdownV2')       # Отправляем сообщение с клавиатурой

                                    
                                    
                                    
            else:                            #обработка обычного текста (не команд)                
                if proc_flag == 2:         #если у пользователя флаг ожидания новой модели -поведения-
                    if message_text == 'отмена':
                        chat.set_proc_flag(chat_id, 1, username)
                        await bot.send_message(chat_id, 'Отменено', reply_markup=types.ReplyKeyboardRemove())      
                    elif message_text == 'очистить':
                        chat.set_proc_flag(chat_id, 1, username)
                        chat.proc_sys_msg(chat_id, 0)
                        await bot.send_message(chat_id, 'Ответы будут стандартными', reply_markup=types.ReplyKeyboardRemove())      
                    else:
                        chat.set_proc_flag(chat_id, 1, username)
                        chat.proc_sys_msg(chat_id, message_text)
                        await bot.send_message(chat_id, 'Новая роль установлена', reply_markup=types.ReplyKeyboardRemove())    
                                          
                elif proc_flag == 3:         #если у пользователя флаг ожидания новой -языковой- модели
                    model_arr = []
                    model_arr.append(config['mainconf']['btn_text_1'])
                    model_arr.append(config['mainconf']['btn_text_2'])
                    model_arr.append(config['mainconf']['btn_text_3'])
                    model_arr.append(config['mainconf']['btn_text_4'])
                    model_arr.append(config['mainconf']['btn_text_5'])
                    model_arr.append(config['mainconf']['btn_text_6'])
                    model_arr.append(config['mainconf']['btn_text_7'])
                    if message_text == 'отмена':
                        chat.set_proc_flag(chat_id, 1, username)
                        await bot.send_message(chat_id, 'Отменено', reply_markup=types.ReplyKeyboardRemove())         
                    elif message_text in model_arr:
                        chat.set_proc_flag(chat_id, 1, username)
                        chat.proc_lang_model(chat_id, message_text)
                        await bot.send_message(chat_id, 'Новая языковая модель установлена', reply_markup=types.ReplyKeyboardRemove()) 
                    else:   
                        chat.set_proc_flag(chat_id, 1, username)
                        await bot.send_message(chat_id, 'Такой нет 😠', reply_markup=types.ReplyKeyboardRemove()) 
                        
                    
                else: # просто запрос 
                    await question_for_ai(chat_id, username, message_text)
                 
            

#-------------------------------------------------------------------------------------------------------------



logger.info(f"Скрипт запущен")

# Запуск бота
async def main():
    await bot.polling()
    

if __name__ == "__main__":
    asyncio.run(main())







