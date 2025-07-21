import discord
import os
import requests
import asyncio
from dotenv import load_dotenv
from discord.ext import commands

# Загрузка переменных окружения
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
TWITCH_USERNAME = os.getenv('TWITCH_USERNAME')
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')

GIF_URL = "https://media.giphy.com/media/xT9IgzoKnwFNmISR8I/giphy.gif"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

stream_live = False  # Состояние стрима

# Получение Twitch access token
def get_twitch_access_token():
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, params=params)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print("Ошибка при получении токена:", response.status_code, response.text)
        return None

# Получение информации о стриме
def get_stream_info():
    access_token = get_twitch_access_token()
    if not access_token:
        return None

    url = f"https://api.twitch.tv/helix/streams?user_login={TWITCH_USERNAME}"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json().get('data')
        if data:
            stream = data[0]
            return stream['game_name'], stream['viewer_count']
        else:
            return None
    else:
        print("Ошибка получения информации о стриме:", response.status_code, response.text)
        return None

# Запуск цикла проверки стрима
async def check_stream_loop():
    global stream_live
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)

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
    print(f"Бот запущен как {bot.user}")
    bot.loop.create_task(check_stream_loop())

bot.run(DISCORD_TOKEN)
