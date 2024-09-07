import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.types import ForumTopic, FSInputFile
from aiogram.utils.media_group import MediaGroupBuilder
import sqlite3
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv


load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("SUPPORT_GROUP_ID"))

MESSAGE_START = os.getenv("MESSAGE_START")
MESSAGE_REQUEST_ACCEPTED = os.getenv("MESSAGE_REQUEST_ACCEPTED")
MESSAGE_CLOSE_REQ = os.getenv("MESSAGE_CLOSE_REQ")

logging.basicConfig(level=logging.INFO)

storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=storage)

conn = sqlite3.connect("support_bot.db")
cursor = conn.cursor()

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS topics
(user_id INTEGER PRIMARY KEY, topic_id INTEGER)
"""
)
conn.commit()


class SupportStates(StatesGroup):
    waiting_for_question = State()
    in_conversation = State()


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer(MESSAGE_START)
    await state.set_state(SupportStates.waiting_for_question)


async def forward_media_to_support(message: types.Message, topic_id: int):
    if message.photo:
        await bot.send_photo(
            GROUP_ID,
            message.photo[-1].file_id,
            caption=message.caption,
            message_thread_id=topic_id,
        )
    elif message.video:
        await bot.send_video(
            GROUP_ID,
            message.video.file_id,
            caption=message.caption,
            message_thread_id=topic_id,
        )
    elif message.document:
        await bot.send_document(
            GROUP_ID,
            message.document.file_id,
            caption=message.caption,
            message_thread_id=topic_id,
        )
    elif message.voice:
        await bot.send_voice(
            GROUP_ID,
            message.voice.file_id,
            caption=message.caption,
            message_thread_id=topic_id,
        )
    elif message.audio:
        await bot.send_audio(
            GROUP_ID,
            message.audio.file_id,
            caption=message.caption,
            message_thread_id=topic_id,
        )


async def get_or_create_topic(message: types.Message) -> int:
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    username = message.from_user.username

    cursor.execute("SELECT topic_id FROM topics WHERE user_id = ?", (user_id,))
    existing_topic = cursor.fetchone()

    if existing_topic:
        topic_id = existing_topic[0]
        # Проверяем, существует ли тема в группе
        try:
            await bot.get_chat(GROUP_ID)
            return topic_id
        except:
            # Если тема не существует, удаляем старую запись
            cursor.execute("DELETE FROM topics WHERE user_id = ?", (user_id,))
            conn.commit()

    # Создаем новую тему
    topic = await bot.create_forum_topic(GROUP_ID, f"Вопрос от {user_name}")
    topic_id = topic.message_thread_id

    # Отправляем информацию о пользователе в новую тему
    user_info = (
        f"Новый запрос в поддержку:\n\n"
        f"Имя: {user_name}\n"
        f"ID: {user_id}\n"
        f"Username: @{username}"
        if username
        else "Отсутствует"
    )

    await bot.send_message(GROUP_ID, user_info, message_thread_id=topic_id)

    cursor.execute("INSERT OR REPLACE INTO topics VALUES (?, ?)", (user_id, topic_id))
    conn.commit()
    return topic_id


@dp.message(SupportStates.waiting_for_question)
@dp.message(SupportStates.in_conversation)
async def process_user_message(message: types.Message, state: FSMContext):
    if message.from_user.is_bot:
        return  # Игнорируем сообщения от ботов
    topic_id = await get_or_create_topic(message)

    if message.text:
        await bot.send_message(GROUP_ID, message.text, message_thread_id=topic_id)
    else:
        await forward_media_to_support(message, topic_id)

    current_state = await state.get_state()
    if current_state == SupportStates.waiting_for_question:
        await message.answer(MESSAGE_REQUEST_ACCEPTED)
        await state.set_state(SupportStates.in_conversation)


@dp.message(Command("close"))
async def cmd_close(message: types.Message):
    if message.chat.id == GROUP_ID:
        topic_id = message.message_thread_id
        cursor.execute("SELECT user_id FROM topics WHERE topic_id = ?", (topic_id,))
        result = cursor.fetchone()
        if result:
            user_id = result[0]
            await bot.send_message(
                user_id,
                MESSAGE_CLOSE_REQ,
            )
            cursor.execute("DELETE FROM topics WHERE topic_id = ?", (topic_id,))
            conn.commit()
            await bot.close_forum_topic(GROUP_ID, topic_id)
            await message.answer("Тема закрыта.")
        else:
            await message.answer("Не удалось найти пользователя для этой темы.")


@dp.message(lambda message: message.chat.id == GROUP_ID)
async def handle_admin_message(message: types.Message):
    if message.from_user.is_bot:
        return  # Игнорируем сообщения от ботов
    if message.reply_to_message:
        topic_id = message.message_thread_id
        cursor.execute("SELECT user_id FROM topics WHERE topic_id = ?", (topic_id,))
        result = cursor.fetchone()
        if result:
            user_id = result[0]
            if message.text:
                await bot.send_message(user_id, message.text)
            elif message.photo:
                await bot.send_photo(
                    user_id, message.photo[-1].file_id, caption=message.caption
                )
            elif message.video:
                await bot.send_video(
                    user_id, message.video.file_id, caption=message.caption
                )
            elif message.document:
                await bot.send_document(
                    user_id, message.document.file_id, caption=message.caption
                )
            elif message.voice:
                await bot.send_voice(
                    user_id, message.voice.file_id, caption=message.caption
                )
            elif message.audio:
                await bot.send_audio(
                    user_id, message.audio.file_id, caption=message.caption
                )
        else:
            await message.answer("Не удалось найти пользователя для этой темы.")


@dp.message()
async def handle_all_message(message: types.Message, state: FSMContext):
    if message.from_user.is_bot:
        return  # Игнорируем сообщения от ботов

    await process_user_message(message, state)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
