import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import yt_dlp
import os

logging.basicConfig(level=logging.INFO)

TOKEN = "6125133441:AAH1DmGzp-MyNUlR2S_48ce4jveDFCC6mqc"
DOWNLOAD_DIR = "downloads"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен и готов к работе!")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id
    logging.info(f"Получено сообщение в чате {chat_id}: {text}")

    if "tiktok.com" not in text:
        # Игнорируем сообщения без ссылок на TikTok
        logging.info("Сообщение не содержит ссылку на TikTok, игнорируем")
        return

    await update.message.reply_text(f"Скачиваю видео с: {text}")

    ydl_opts = {
        'format': 'mp4',
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(text, download=True)
            filename = ydl.prepare_filename(info)
        
        # Отправляем видео в чат
        with open(filename, 'rb') as video_file:
            await context.bot.send_video(chat_id=chat_id, video=video_file)
        
        # Удаляем файл после отправки
        os.remove(filename)
        logging.info("Видео отправлено и файл удалён")
    except Exception as e:
        logging.error(f"Ошибка при скачивании: {e}")
        await update.message.reply_text(f"Ошибка при скачивании: {e}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_video))

    app.run_polling()

if __name__ == '__main__':
    main()
