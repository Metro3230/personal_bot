from dotenv import load_dotenv
from openai import AsyncOpenAI
from pathlib import Path
import os
import configparser
import requests
from typing import List, Dict, Any

script_dir = Path(__file__).parent  # Определяем путь к текущему скрипту
data_dir = script_dir / 'data'
log_file = script_dir / data_dir / 'log.log'
env_file = script_dir / data_dir / '.env'
config_file = data_dir / 'config.ini'

config = configparser.ConfigParser()  # настраиваем и читаем файл конфига
config.read(config_file)

load_dotenv(env_file)
ai_API_key = os.getenv('OPENAI_API_KEY')    # читаем token ai c .env

# Единый клиент по OpenAI‑совместимому ProxyAPI эндпоинту
client_openai = AsyncOpenAI(
    api_key=ai_API_key,
    base_url=config['AIconf']['openai_API_url'],  # ожидается https://openai.api.proxyapi.ru/v1
    timeout=float(config['AIconf']['ai_req_timeout']),
)


def _get_model_id(label: str) -> str:
    """
    Возвращает provider-prefixed идентификатор модели по человеко-понятной метке (текст кнопки).
    Берётся из секции [models] конфига. Если ключ не найден — возвращаем исходную метку как есть.
    Это даёт обратную совместимость при старых конфигурациях.
    """
    if config.has_section('models') and config.has_option('models', label):
        return config['models'][label]
    return label


def _is_responses_model(model_id: str) -> bool:
    """
    Модели семейства o1/o3 (OpenAI) требуют /v1/responses, а не /v1/chat/completions.
    Здесь определяем простой признак.
    """
    low = model_id.lower()
    return low.startswith('openai/o1') or low.startswith('openai/o3')


def _messages_to_input(msgs: List[Dict[str, Any]]) -> str:
    """
    Конвертация истории чата (OpenAI chat messages) в один текст для /v1/responses.
    Сохраняем роли и порядок.
    """
    parts: List[str] = []
    for m in msgs:
        role = m.get('role', 'user')
        content = m.get('content', '')
        # Некоторые клиенты могут прислать content как список объектов, нормализуем в строку.
        if isinstance(content, list):
            try:
                content = ''.join(
                    x.get('text', '') if isinstance(x, dict) else str(x)
                    for x in content
                )
            except Exception:
                content = str(content)
        parts.append(f"{role}: {content}")
    return "\n\n".join(parts)


def _calc_price(model_label: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Расчёт стоимости на основе price_... из [AIconf].
    Конфиг хранит цены за 1 000 000 токенов.
    Если цена не найдена — считаем 0 для соответствующей части.
    """
    req_price_str = config['AIconf'].get(f'price_{model_label}_req', '0')
    resp_price_str = config['AIconf'].get(f'price_{model_label}_resp', '0')
    try:
        req_price = float(req_price_str)
    except Exception:
        req_price = 0.0
    try:
        resp_price = float(resp_price_str)
    except Exception:
        resp_price = 0.0

    return (prompt_tokens * (req_price / 1_000_000.0)) + (completion_tokens * (resp_price / 1_000_000.0))


async def req_to_ai(msgs: List[Dict[str, Any]], model_label: str):
    """
    Универсальный вызов ИИ:
    - Преобразует метку (кнопку) в provider-prefixed model id по [models]
    - Выбирает правильный эндпоинт: /v1/chat/completions или /v1/responses
    - Возвращает (response_text, price, prompt_tokens_used)
    """
    model_id = _get_model_id(model_label)

    # Ветка для /v1/responses (o1/o3)
    if _is_responses_model(model_id):
        prompt = _messages_to_input(msgs)
        response = await client_openai.responses.create(
            model=model_id,
            input=prompt,
        )

        # Извлекаем usage
        input_tokens = getattr(getattr(response, 'usage', None), 'input_tokens', 0) or 0
        output_tokens = getattr(getattr(response, 'usage', None), 'output_tokens', 0) or 0

        # Извлекаем текст
        response_text = ''
        # В SDK есть удобное свойство output_text (если доступно)
        try:
            response_text = getattr(response, 'output_text', '') or ''
        except Exception:
            response_text = ''

        # Если не удалось — пробуем разобрать output вручную
        if not response_text:
            try:
                output = getattr(response, 'output', None)
                if output:
                    # output — список блоков, собираем текстовые части
                    chunks: List[str] = []
                    for item in output:
                        content = getattr(item, 'content', None)
                        if content and isinstance(content, list):
                            for c in content:
                                t = getattr(getattr(c, 'text', None), 'value', None)
                                if t:
                                    chunks.append(t)
                                else:
                                    # возможные альтернативные структуры
                                    if hasattr(c, 'text') and isinstance(c.text, str):
                                        chunks.append(c.text)
                    response_text = ''.join(chunks)
            except Exception:
                response_text = ''

        # Последний fallback — вдруг прокся вернула в стиле chat.completions
        if not response_text and hasattr(response, 'choices'):
            try:
                response_text = response.choices[0].message.content
            except Exception:
                response_text = ''

        price = _calc_price(model_label, input_tokens, output_tokens)
        return response_text, price, input_tokens

    # Обычные chat.completions
    response = await client_openai.chat.completions.create(
        model=model_id,
        messages=msgs,
    )

    prompt_tokens = getattr(getattr(response, 'usage', None), 'prompt_tokens', 0) or 0
    completion_tokens = getattr(getattr(response, 'usage', None), 'completion_tokens', 0) or 0
    response_text = response.choices[0].message.content

    price = _calc_price(model_label, prompt_tokens, completion_tokens)
    return response_text, price, prompt_tokens


async def get_balance():
    balance_url = config['AIconf']['proxyapi_balance']
    headers = {
        'Authorization': 'Bearer ' + ai_API_key
    }
    response = requests.get(balance_url, headers=headers)
    balance_data = response.json()
    balance = balance_data.get('balance')
    return balance  #возвращаем баланс
