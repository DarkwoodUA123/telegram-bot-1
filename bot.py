import discord
import os
import requests
import asyncio
from dotenv import load_dotenv
from discord.ext import commands

# Загрузка переменных окружения
load_dotenv()

def clean_token(token: str | None) -> str | None:
    """Убирает пробелы и символы = в начале/конце, если есть"""
    if token:
        return token.strip().lstrip('=').strip()
    return None

# Чистим токен, если там лишние символы
DISCORD_TOKEN = clean_token(os.getenv('DISCORD_TOKEN'))
channel_id_str = os.getenv('CHANNEL_ID')
TWITCH_USERNAME = os.getenv('TWITCH_USERNAME')
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET')

print(f"DISCORD_TOKEN: {DISCORD_TOKEN!r}")
print(f"CHANNEL_ID (raw): {channel_id_str!r}")

if DISCORD_TOKEN is None or DISCORD_TOKEN == "":
    raise ValueError("Переменная окружения DISCORD_TOKEN не установлена или пуста!")

if channel_id_str is None:
    raise ValueError("Переменная окружения CHANNEL_ID не установлена.")
try:
    CHANNEL_ID = int(channel_id_str)
except ValueError:
    raise ValueError("CHANNEL_ID должен быть числом.")

# --- дальше твой исходный код без изменений ---
GIF_URL = "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExcjRlYWN6aXZsYnZycTdnN2M4bGI3OXd2c2NkNmltNmpvc2F2Y3F4NyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/HSyR7A954pdC4w6PHa/giphy.gif"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

stream_live = False
stream_message = None  # Для хранения последнего отправленного сообщения

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

async def check_stream_loop():
    global stream_live, stream_message
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)

    while not bot.is_closed():
        stream_info = get_stream_info()
        if stream_info:
            game_name, viewer_count = stream_info
            if not stream_live:
                stream_live = True
                embed = discord.Embed(
                    title=f"🎮 {TWITCH_USERNAME} в эфире! 🔴",
                    description=f"[Смотреть стрим](https://www.twitch.tv/{TWITCH_USERNAME})",
                    color=discord.Color.red())
                embed.add_field(name="Игра:", value=game_name, inline=True)
                embed.add_field(name="Зрителей:", value=viewer_count, inline=True)
                embed.set_thumbnail(url="https://static-cdn.jtvnw.net/jtv_user_pictures/twitch_profile_image.png")
                embed.set_image(url=GIF_URL)
                embed.set_footer(text="Бот создан | stupapupa___")

                stream_message = await channel.send("@everyone 🦄 Приветики! Стрим онлайн💜 Заходи скорее!", embed=embed)
            else:
                if stream_message:
                    new_embed = discord.Embed(
                        title=f"🎮 {TWITCH_USERNAME} в эфире! 🔴",
                        description=f"[Смотреть стрим](https://www.twitch.tv/{TWITCH_USERNAME})",
                        color=discord.Color.red())
                    new_embed.add_field(name="Игра:", value=game_name, inline=True)
                    new_embed.add_field(name="Зрителей:", value=viewer_count, inline=True)
                    new_embed.set_thumbnail(url="https://static-cdn.jtvnw.net/jtv_user_pictures/twitch_profile_image.png")
                    new_embed.set_image(url=GIF_URL)
                    new_embed.set_footer(text="Бот создан | stupapupa___")

                    await stream_message.edit(embed=new_embed)
        else:
            stream_live = False
            stream_message = None

        await asyncio.sleep(10)

@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user.name}")
    bot.loop.create_task(check_stream_loop())

@bot.command(name='say')
async def say(ctx, *, message: str):
    await ctx.send(message)

@bot.command(name='testnotify')
async def test_notify(ctx):
    channel = bot.get_channel(CHANNEL_ID)
    game_name = "Test Game"
    viewer_count = 123

    embed = discord.Embed(
        title=f"🎮 {TWITCH_USERNAME} в эфире! 🔴",
        description=f"[Смотреть стрим](https://www.twitch.tv/{TWITCH_USERNAME})",
        color=discord.Color.red())
    embed.add_field(name="Игра:", value=game_name, inline=True)
    embed.add_field(name="Зрителей:", value=viewer_count, inline=True)
    embed.set_thumbnail(url="https://static-cdn.jtvnw.net/jtv_user_pictures/twitch_profile_image.png")
    embed.set_image(url=GIF_URL)
    embed.set_footer(text="Вопросы по боту в дс -> | stupapupa___")

    await channel.send("**ЭТО ТЕСТ ОПОВЕЩЕНИЕ**\n🦄 Приветики! Стрим онлайн💜 Заходи скорее!", embed=embed)

bot.run(DISCORD_TOKEN)
