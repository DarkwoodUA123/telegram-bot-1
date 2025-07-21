import discord
import os
import requests
import asyncio
from dotenv import load_dotenv
from discord.ext import commands

# Загружаем .env и переменные окружения
load_dotenv()

# Отладочный вывод всех переменных окружения (кроме токенов)
print("=== DEBUG: Переменные окружения ===")
for k, v in os.environ.items():
    if "TOKEN" not in k and "SECRET" not in k:
        print(f"{k} = {v}")
print("=== Конец вывода ===")

def get_env_var(name, required=True):
    value = os.getenv(name)
    if value is None or value.strip() == "":
        if required:
            raise ValueError(f"❌ Переменная окружения {name} не установлена или пуста")
        return None
    return value.strip(" =")  # убираем пробелы и лишние '='

try:
    DISCORD_TOKEN = get_env_var('DISCORD_TOKEN')
    CHANNEL_ID = int(get_env_var('CHANNEL_ID'))
    TWITCH_USERNAME = get_env_var('TWITCH_USERNAME')
    TWITCH_CLIENT_ID = get_env_var('TWITCH_CLIENT_ID')
    TWITCH_CLIENT_SECRET = get_env_var('TWITCH_CLIENT_SECRET')
except ValueError as e:
    print(f"[Ошибка запуска] {e}")
    exit(1)

GIF_URL = "https://media.giphy.com/media/xT9IgzoKnwFNmISR8I/giphy.gif"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

stream_live = False  # Состояние стрима

def get_twitch_access_token():
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        print(f"Ошибка при получении токена Twitch: {e}")
        return None

def get_stream_info():
    access_token = get_twitch_access_token()
    if not access_token:
        return None

    url = f"https://api.twitch.tv/helix/streams?user_login={TWITCH_USERNAME}"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json().get('data')
        if data:
            stream = data[0]
            return stream['game_name'], stream['viewer_count']
        else:
            return None
    except Exception as e:
        print(f"Ошибка получения информации о стриме: {e}")
        return None

async def check_stream_loop():
    global stream_live
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)

    if channel is None:
        print(f"❌ Канал с ID {CHANNEL_ID} не найден. Проверь, что бот имеет доступ.")
        return

    while not bot.is_closed():
        stream_info = get_stream_info()
        if stream_info:
            if not stream_live:
                stream_live = True
                game_name, viewer_count = stream_info
                embed = discord.Embed(
                    title=f"🎮 {TWITCH_USERNAME} в эфире! 🔴",
                    description=f"[Смотреть стрим](https://www.twitch.tv/{TWITCH_USERNAME})",
                    color=discord.Color.red()
                )
                embed.add_field(name="Игра:", value=game_name, inline=True)
                embed.add_field(name="Зрителей:", value=viewer_count, inline=True)
                embed.set_thumbnail(url="https://static-cdn.jtvnw.net/jtv_user_pictures/twitch_profile_image.png")
                embed.set_image(url=GIF_URL)
                embed.set_footer(text="Создано ботом | stupapupa___")
                await channel.send("@everyone", embed=embed)
        else:
            stream_live = False

        await asyncio.sleep(10)

@bot.event
async def on_ready():
    print(f"✅ Бот запущен как {bot.user}")
    bot.loop.create_task(check_stream_loop())

bot.run(DISCORD_TOKEN)
