
# Теоеграм Бот
***
Бот проверяет статус задания отправленного на ревью и присылает уведомление с изменением статуса

## Стек
***
Python3, API, telegram

## Инструкция по запуску
***
* Клонируем репозиторий

	`
	git clone git@github.com:EgorFedotov/homework_bot.git
	`


* Устанавливаем и активируем виртуальное окружение  

	`
    py -3.7 -m venv venv
    `
    `
    source venv/Scripts/activate
    `
   
   
* Устанавливаем зависимости из файла requirements.txt
 
	`
    pip install -r requirements.txt
    `
 

* Записать в файл .env необходимые ключи

    токен профиля на Яндекс.Практикуме
    токен телеграм-бота
    свой ID в телеграме


* запускаем сервер 

    `
	python homework.py
    `
