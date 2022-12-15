import logging
import os
import sys
import time
from http import HTTPStatus
from logging import StreamHandler

from dotenv import load_dotenv
import telegram
import requests

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
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        return True
    return False


def send_message(bot, message):
    """отправка сообщения."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.error.TelegramError:
        logger.error('Сообщение не отправлено')
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
    except requests.exceptions.RequestException as error:
        raise exceptions.ResponseStatusError(f'Эндпоинт недоступен {error}')
    if homework_statuses.status_code == HTTPStatus.OK:
        try:
            return homework_statuses.json()
        except requests.exceptions.JSONDecodeError:
            raise exceptions.ResponseStatusError('Сбой декодирования JSON')
    else:
        raise exceptions.ResponseStatusError('API в данный момент недоступен')


def check_response(response):
    """получение статуса домашней работы."""
    if not isinstance(response, dict):
        raise TypeError('Получены данные не ввиде словаря')
    if 'homeworks' not in response:
        raise KeyError('Нет ключа homeworks')
    if not isinstance(response['homeworks'], list):
        raise TypeError('Получены данные homeworks не ввиде списка')
    if not isinstance(response['current_date'], int):
        raise TypeError('Получены данные current_date не ввиде числа')
    if response['homeworks'] == []:
        raise exceptions.EmptyHomeworksList


def parse_status(homework):
    """получение вердикта работы."""
    if 'homework_name' not in homework:
        raise KeyError('Нет ключа homework_name')
    homework_name = homework['homework_name']
    if 'status' not in homework:
        raise KeyError('Нет ключа status')
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError(
            f'Получен неизвестный статус домашней работы - {homework_status}'
        )
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        logger.critical('Отсутствует переменная окружения!')
        sys.exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    previous_message = None
    while True:
        try:
            homeworks = get_api_answer(timestamp)
            check_response(homeworks)
            homework = homeworks.get('homeworks')[0]
            message = parse_status(homework)
            timestamp = homeworks.get('current_date')
        except exceptions.EmptyHomeworksList:
            logger.debug('Cтатус задания не обновлялся')
            message = 'Cтатус задания не обновлялся'
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error('Сбой в работе программы:')
        finally:
            if previous_message != message:
                send_message(bot, message)
                previous_message = message
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
