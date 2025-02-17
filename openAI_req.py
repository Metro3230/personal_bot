from dotenv import load_dotenv
from openai import AsyncOpenAI
from pathlib import Path
# from config import AIconf
import os
import configparser

script_dir = Path(__file__).parent  # Определяем путь к текущему скрипту
data_dir = script_dir / 'data'
log_file = script_dir / data_dir / 'log.log'
env_file = script_dir / data_dir / '.env'
config_file = data_dir / 'config.ini'

config = configparser.ConfigParser()  # настраиваем и читаем файл конфига
config.read(config_file)

load_dotenv(env_file)
ai_API_key = os.getenv('OPENAI_API_KEY')    # читаем token ai c .env
 
client_openai = AsyncOpenAI(
    api_key=ai_API_key,
    base_url=config['AIconf']['openai_API_url'],
    timeout=float(config['AIconf']['ai_req_timeout']),
) 

client_deepseek = AsyncOpenAI(
    api_key=ai_API_key,
    base_url=config['AIconf']['deepseek_API_url'],
    timeout=float(config['AIconf']['ai_req_timeout']),
)




async def req_to_openai(msgs, model='gpt-4o'):
    
    response = await client_openai.chat.completions.create(
                model=model,
                messages=msgs,
                )
    
    response_req_tokens = response.usage.prompt_tokens        #парсим кол-вы токенов на запрос и сам ответ   
    response_resp_price = response.usage.completion_tokens        
    response_text = response.choices[0].message.content
    
    req_price = float(config['AIconf'][f'price_{model}_req'])     #стоимости запроса и ответа из config.ini
    resp_price = float(config['AIconf'][f'price_{model}_resp'])
    
    price = (response_req_tokens * (req_price / 1000)) + (response_resp_price * (resp_price / 1000))
        
    return response_text, price, response_req_tokens  #отдаём текст ответа, цену, 




async def req_to_deepseek(msgs, model='deepseek-chat'):
    
    response = await client_deepseek.chat.completions.create(
                model=model,
                messages=msgs,
                )
    
    response_req_tokens = response.usage.prompt_tokens        #парсим кол-во токенов на запрос и сам ответ   
    response_resp_price = response.usage.completion_tokens        
    response_text = response.choices[0].message.content
    
    req_price = float(config['AIconf'][f'price_{model}_req'])     #стоимости запроса и ответа из config.ini
    resp_price = float(config['AIconf'][f'price_{model}_resp'])
    
    price = (response_req_tokens * (req_price / 1000)) + (response_resp_price * (resp_price / 1000))
        
    return response_text, price, response_req_tokens  #отдаём текст ответа, цену, 












# # # ======================================================================тест обычного запроса
# zapros = [
#         {
#             "role": "user",
#             "content": "Привет."
#         }
#     ]

# # model = "o3-mini"    

# # Вызов асинхронной функции для отладки
# import asyncio
# if __name__ == "__main__":
#     response_text, rub_price, wind_tokens = asyncio.run(req_to_openai(zapros))

#     print('openai')
#     print(response_text)
#     print(wind_tokens)    
#     print(rub_price)
    
    
# import asyncio
# if __name__ == "__main__":
#     response_text, rub_price, wind_tokens = asyncio.run(req_to_deepseek(zapros))

#     print('deepseek')
#     print(response_text)
#     print(wind_tokens)    
#     print(rub_price)












