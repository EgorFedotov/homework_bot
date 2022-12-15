class EmptyHomeworksList(Exception):
    """Ошибки при работе телеграмм бота."""

    pass


class ResponseStatusError(Exception):
    '''Неожиданный код ответа API.'''
    pass


class MessageNotSent(Exception):
    '''сообщение не отправлено.'''
    pass


class ResponseStatusCode(Exception):
    '''Ошибка запроса к API.'''
    pass


class InvalidRequestApi(Exception):
    '''Некорректный статус запроса API.'''


class CheckKeyHw(Exception):
    '''Исключение неправильного формата ответа API.'''


class UnknownHWStatusException(Exception):
    """Unknown homework status exception."""
    pass
