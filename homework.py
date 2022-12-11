import logging
import os
import time
from logging import StreamHandler

from dotenv import load_dotenv
import telegram
import requests

load_dotenv()


PRACTICUM_TOKEN = os.getenv('RACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_PERIOD: int = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
PAYLOAD = {'from_date': int(time.time())}
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
            '%(asctime)s:: %(levelname)s:: %(name)s:: %(message)s'
        )
    )
    logger.addHandler(handler)
    return logger


logger = add_logger(__name__)


def check_tokens():
    """Проверка переменных окружения."""
    if (PRACTICUM_TOKEN is None
            or TELEGRAM_TOKEN is None
            or TELEGRAM_CHAT_ID is None):
        logger.critical('Ошибка в переменных окружения')
        raise ValueError


def send_message(bot, message):
    """отправка сообщения."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug('Сообщение отправлено')
    except Exception as error:
        logger.error(f'сообщение не отправленно {error}')


def get_api_answer(timestamp):
    """запрос к серверу ЯП."""
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=PAYLOAD
        )
    except Exception as error:
        logger.error(f'Яндекс.Практикум вернул ошибку: {error}')
    if homework_statuses.status_code == 200:
        return homework_statuses.json()
    else:
        logger.error('Сервер ЯП не доступен')
        raise Exception


def check_response(response):
    """получение статуса домашней работы."""
    try:
        response['homeworks']
    except KeyError:
        logger.error('Нет ключа homeworks')
        raise KeyError('Нет ключа homeworks')
    try:
        response['current_date']
    except KeyError:
        logger.error('Нет ключа current_date')
        raise KeyError('Нет ключа current_date')
    if not isinstance(response, dict):
        logger.error('Не тот тип данных в запросе')
        raise TypeError('Не тот тип данных в запросе')
    if not isinstance(response['homeworks'], list):
        logger.error('Не тот тип данных в запросе')
        raise TypeError('Не тот тип данных в запросе')
    return response['homeworks']


def parse_status(homework):
    """получение вердикта работы."""
    try:
        homework_name = homework['homework_name']
    except KeyError:
        logger.error('Неверный ответ сервера')
    homework_status = homework.get('status')
    try:
        verdict = HOMEWORK_VERDICTS[homework['status']]
    except KeyError:
        raise KeyError(f' неизвестный статус {homework_status}')
        return (f'нет такого статуса {homework_status}')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    timestamp = PAYLOAD['from_date']
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            homeworks = get_api_answer(timestamp)
            check_response(homeworks)
            homeworks_list = homeworks.get('homeworks')
            for homework in homeworks_list:
                send_message(bot, parse_status(homework))
                logger.debug('Сообщение отправлено:', parse_status(homework))
        except Exception as error:
            send_message(bot, f'Сбой в работе программы: {error}')
            logger.error(f'Сбой в работе программы: {error}')
            time.sleep(RETRY_PERIOD)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
