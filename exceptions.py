class EmptyHomeworksList(Exception):
    """Ошибки при работе телеграмм бота."""

    pass


class ResponseStatusError(Exception):
    '''Неожиданный код ответа API.'''
    pass
