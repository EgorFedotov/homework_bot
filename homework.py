import logging
import os
import sys
import time
from http import HTTPStatus
from json.decoder import JSONDecodeError
from logging import StreamHandler

import requests
import telegram
from dotenv import load_dotenv

import exceptions

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_PERIOD: int = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def add_logger(name):
    """создание логов."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s:: %(levelname)s:: %(name)s:: %(message)s %(lineno)d'
        )
    )
    logger.addHandler(handler)
    return logger


logger = add_logger(__name__)


def check_tokens():
    """Проверка переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """отправка сообщения."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.error.TelegramError as error:
        logger.error(f'Сообщение не отправлено {error}')
    else:
        logger.debug('Сообщение отправлено')


def get_api_answer(timestamp):
    """запрос к серверу ЯП."""
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': f'{timestamp}'}
        )
        if homework_statuses.status_code != HTTPStatus.OK:
            raise exceptions.ResponseStatusError(
                f'API недоступен, статус код - {homework_statuses.status_code}'
            )
        return homework_statuses.json()
    except JSONDecodeError as error:
        raise exceptions.ResponseStatusError(f'Сбой JSON в ответе: {error}')
    except requests.exceptions.RequestException as error:
        raise exceptions.ResponseStatusError(f'Эндпоинт недоступен {error}')


def check_response(response):
    """получение статуса домашней работы."""
    if not isinstance(response, dict):
        raise TypeError('Получены данные не в виде словаря')
    if 'homeworks' not in response:
        raise KeyError('Нет ключа homeworks')
    if not isinstance(response['homeworks'], list):
        raise TypeError('Получены данные homeworks не в виде списка')
    if 'current_date' not in response:
        raise exceptions.DateNotValid('нет  ключа current_date')
    if not isinstance(response['current_date'], int):
        raise exceptions.DateNotValid('Ключ current_date не в виде числа')
    return response['homeworks']


def parse_status(homework):
    """получение вердикта работы."""
    if 'homework_name' not in homework:
        raise KeyError('Нет ключа homework_name')
    homework_name = homework['homework_name']
    if 'status' not in homework:
        raise KeyError('Нет ключа status')
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(
            f'Получен неизвестный статус домашней работы - {homework_status}'
        )
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отсутствует переменная окружения!')
        sys.exit('Программа остановлена, отсутствуют переменные окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    previous_message = None
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                homework = response['homeworks'][0]
                send_message(bot, parse_status(homework))
            timestamp = response.get('current_date')
        except exceptions.DataNotValid as error:
            logger.error(f'Дата проверки изменений некорректна: {error}')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(f'Сбой в работе программы {error}')
            if previous_message != message:
                send_message(bot, message)
                previous_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
