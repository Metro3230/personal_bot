import json
import os
from datetime import datetime
from pathlib import Path
import shutil
# from config import chatconf
import configparser

script_dir = Path(__file__).parent  # Определяем путь к текущему скрипту
data_dir = script_dir / 'data'
msg_hist_dir = script_dir / 'data/msg_hits'   #папка с историями сообщений
msg_arch_dir = msg_hist_dir / 'archive'    #папка с историями удалившихся пользователей
config_file = data_dir / 'config.ini'
template_file = msg_hist_dir / 'template_json.txt'

config = configparser.ConfigParser()  # настраиваем и читаем файл конфига
config.read(config_file)



def save_message_to_json(chat_id, role, message, price=0, sender_name=None): #добавление сообщения

    file_name = f"{msg_hist_dir}/{chat_id}.json"    # Формируем имя файла

    new_message = {    # Структура нового сообщения
        "role": role,
        "content": message
    }

    if os.path.isfile(file_name):     # Если файл существует
        with open(file_name, mode='r', encoding='utf-8') as file:  #, загружаем существующие данные
            data = json.load(file)
    else:       # Если файл не существует, создаем со структурой:
        today_date = datetime.now().strftime('%Y-%m-%d')   
        data = {
            "Sender Name": sender_name,
            "Behavior Flag": 0,
            "Total Cost": 0,
            "First Date": today_date,
            "Language Model": "gpt-4o",
            "System Message": None,
            "Messages": []
        }

    data["Total Cost"] += price    # Увеличиваем счётчик денег
    data["Total Cost"] = round(data["Total Cost"], 10)   #немного округляем на всякий

    data["Messages"].append(new_message)    # Добавляем новое сообщение в массив "Messages"

    with open(file_name, mode='w', encoding='utf-8') as file:    # Сохраняем обновленные данные обратно в файл
        json.dump(data, file, ensure_ascii=False, indent=4)
        
        
        

def get_stat(chat_id): #статистика
    file_name = f"{msg_hist_dir}/{chat_id}.json"    # Формируем имя файла

    if os.path.isfile(file_name):     # Если файл существует
        with open(file_name, mode='r', encoding='utf-8') as file:  #, загружаем существующие данные
            data = json.load(file)
    else:
        return 0     # Если файл не существует, отдаём 0
        
    total_cost = data.get("Total Cost")
    language_model = data.get("Language Model")
    role = data.get("System Message")

        
    return total_cost, language_model, role   #возвращаем цену всего, языковую модель, роль
        
    
    

def get_context(chat_id): #извлечение контекста переписки
    
    file_name = f"{msg_hist_dir}/{chat_id}.json"    # Формируем имя файла
        
    if os.path.isfile(file_name):    # Проверяем, существует ли файл
        
        with open(file_name, mode='r', encoding='utf-8') as file:    # Загружаем данные из файла
            data = json.load(file)
            
        messages = data.get("Messages", [])    # Извлекаем массив сообщений
        
        role = {'role': 'system', 'content': f'{data["System Message"]}'}        
        if (data["System Message"]):
            messages.insert(0, role)
                 
        return messages
    
    else:
        return False #лож, если файла нет
        
     

def remove_context(chat_id): #очистка контекста

    file_name = f"{msg_hist_dir}/{chat_id}.json"    # Формируем имя файла

    if os.path.isfile(file_name):     # Если файл существует
        with open(file_name, mode='r', encoding='utf-8') as file:  #, загружаем существующие данные
            data = json.load(file)
            
        data["Messages"] = []  # пустой массив в..  
           
        with open(file_name, mode='w', encoding='utf-8') as file:    # Сохраняем обновленные данные обратно в файл
            json.dump(data, file, ensure_ascii=False, indent=4)
     
     
     
     
def proc_sys_msg(chat_id, sys_msg=None): # обработка системного сообщения (если второй аргумент не передан - возвращает факт состояние ,если передан - меняет состояние на переданный, если второй аргумент 0 - выставляем в поле роли None )

    file_name = f"{msg_hist_dir}/{chat_id}.json"    # Формируем путь файла

    if os.path.isfile(file_name):     # Если файл существует
        with open(file_name, mode='r', encoding='utf-8') as file:  #, загружаем существующие данные
            data = json.load(file)
        
        if sys_msg is not None:
            if sys_msg == 0:
                data["System Message"] = None  # присвоить none, так как 0        
            else:            
                data["System Message"] = sys_msg  # присвоить переданное        
            with open(file_name, mode='w', encoding='utf-8') as file:    # Сохраняем обновленные данные обратно в файл
                json.dump(data, file, ensure_ascii=False, indent=4)
            
        else:
            return data["System Message"]     
          
     
def proc_lang_model(chat_id, new_lang_model=None): # обработка языковой модели (если второй аргумент не передан - возвращает факт состояние ,если передан - меняет состояние на переданный )

    file_name = f"{msg_hist_dir}/{chat_id}.json"    # Формируем путь файла

    if os.path.isfile(file_name):     # Если файл существует
        with open(file_name, mode='r', encoding='utf-8') as file:  #, загружаем существующие данные
            data = json.load(file)
        
        if new_lang_model is not None:
            
            data["Language Model"] = new_lang_model  # присвоить (если что то передали функции)            
            with open(file_name, mode='w', encoding='utf-8') as file:    # Сохраняем обновленные данные обратно в файл
                json.dump(data, file, ensure_ascii=False, indent=4)
            
        else:
            return data["Language Model"]     

     
     
def set_proc_flag(chat_id, variable, sender_name=None): # установить флаг состояния ожидания ответа      

    file_name = f"{msg_hist_dir}/{chat_id}.json"    # Формируем имя файла

    if os.path.isfile(file_name):     # Если файл существует
        with open(file_name, mode='r', encoding='utf-8') as file:  #, загружаем существующие данные
            data = json.load(file)
    else:       # Если файл не существует, создаем со структурой:
        today_date = datetime.now().strftime('%Y-%m-%d')   
        data = {
            "Sender Name": sender_name,
            "Behavior Flag": 0,
            "Total Cost": 0,
            "First Date": today_date,
            "Language Model": "gpt-4o",
            "System Message": None,
            "Messages": []
        }
                    
    data["Behavior Flag"] = variable  # присвоить состояние флага (если что то передали функции)            
    with open(file_name, mode='w', encoding='utf-8') as file:    # Сохраняем обновленные данные обратно в файл
        json.dump(data, file, ensure_ascii=False, indent=4)
            
     
     
def get_proc_flag(chat_id): # флаг состояния ожидания ответа (0 если файла чата не существует)
    
    # 0 - пароль не введён
    # 1 - стандартная переписка
    # 2 - ожидание нового системного сообщения (новой модели поведения)
    # 3 - ожидание новой языковой модели

    file_name = f"{msg_hist_dir}/{chat_id}.json"    # Формируем имя файла

    if os.path.isfile(file_name):     # Если файл существует
        with open(file_name, mode='r', encoding='utf-8') as file:  #, загружаем существующие данные
            data = json.load(file)
        return data["Behavior Flag"]
    else:       # Если файл не существует
        return 0








