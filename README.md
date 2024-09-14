
# Support Bot

Этот бот создан для обеспечения удобной поддержки пользователей через Telegram. Он позволяет пользователям отправлять сообщения в службу поддержки, а администраторам отвечать на них в групповом чате. Все обращения удобно разделены на ветки.

![support test](/.github/image.png)

### Основной концепт
Удобно разделить обращения по темам в группе

## Возможности

* **Создание тем:** При первом обращении пользователя бот автоматически создает новую тему в указанной группе поддержки.
* **Пересылка сообщений:** Все сообщения от пользователя (текст, фото, видео, документы, голосовые и аудио сообщения) пересылаются в тему поддержки.
* **Ответы администраторов:** Администраторы могут отвечать на сообщения пользователей прямо из группового чата.
* **Закрытие тем:** Администраторы могут закрывать темы с помощью команды `/close`.

## Настройка
Файл .env.example содержит пример конфигурации бота:

 - **BOT_TOKEN**: Токен вашего бота из [@BotFather](https://t.me/BotFather).

 - **SUPPORT_GROUP_ID**: ID группы поддержки, куда будут пересылаться запросы.
 - **MESSAGE_START**: Приветственное сообщение бота.
 - **MESSAGE_REQUEST_ACCEPTED**: Сообщение о принятии запроса.
 - **MESSAGE_CLOSE_REQ**: Сообщение о закрытии запроса.
 - **DELETE_AFTER_CLOSING и DELETE_DELAY**: удалять ли ветку после закрытия и с какой задержкой.

Скопируйте .env.example в .env и заполните значения.