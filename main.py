import disnake
import asyncio
from disnake.ext import commands, tasks
from config import TOKEN  # Import TOKEN from config.py
from music import setup_music_commands  # Импортируем музыкальный функционал

# server ID and voice channel ID, to observe
GUILD_ID = 607877371416150041  # ID вашего сервера
VOICE_CHANNEL_IDS = [690479552056786954]  # ID голосовых каналов
MAX_PARTICIPANTS = 3  # Лимит участников

ALLOWED_CHANNEL_ID = 608659506922127420  # ID текстового канала для взаимодействия с ботом

# Intent'ы
intents = disnake.Intents.all()

# Создаём бота
bot = commands.Bot(command_prefix="!", intents=intents, test_guilds=[GUILD_ID])  # test_guilds для быстрого синка команд


# Флаг для контроля мониторинга
monitoring_enabled = False

# Подключаем музыкальные команды
setup_music_commands(bot)

# Событие при запуске бота
@bot.event
async def on_ready():
    print(f"✅ Бот запущен как {bot.user}")


# Команда /ping
@bot.slash_command(name="ping", description="Проверка работоспособности бота")
async def ping(inter: disnake.ApplicationCommandInteraction):
    if inter.channel.id != ALLOWED_CHANNEL_ID:
        return
    await inter.response.send_message("🏓 Pong!")


# Команда /enable_monitor
@bot.slash_command(name="enable_monitor", description="Включить мониторинг участников")
async def enable_monitor(inter: disnake.ApplicationCommandInteraction):
    global monitoring_enabled
    if inter.channel.id != ALLOWED_CHANNEL_ID:
        return
    if not monitoring_enabled:
        monitoring_enabled = True
        monitor_channels.start()
        await inter.response.send_message("🔍 Мониторинг участников включён.")
    else:
        await inter.response.send_message("🔍 Мониторинг уже включён.")


# Команда /disable_monitor
@bot.slash_command(name="disable_monitor", description="Отключить мониторинг участников")
async def disable_monitor(inter: disnake.ApplicationCommandInteraction):
    global monitoring_enabled
    if inter.channel.id != ALLOWED_CHANNEL_ID:
        return
    if monitoring_enabled:
        monitoring_enabled = False
        monitor_channels.stop()
        await inter.response.send_message("🛑 Мониторинг участников отключён.")
    else:
        await inter.response.send_message("🛑 Мониторинг уже отключён.")


# Цикл для мониторинга каналов
@tasks.loop(seconds=10)
async def monitor_channels():
    if not monitoring_enabled:
        return

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("Сервер не найден.")
        return

    for channel_id in VOICE_CHANNEL_IDS:
        voice_channel = guild.get_channel(channel_id)
        if voice_channel:
            participant_count = len(voice_channel.members)
            print(f"Канал {voice_channel.name}: {participant_count} участников")

            overwrite = voice_channel.overwrites_for(guild.default_role)
            if participant_count < MAX_PARTICIPANTS:
                if not overwrite.stream:
                    overwrite.stream = True
                    await voice_channel.set_permissions(guild.default_role, overwrite=overwrite)
                    print(f"✅ Стриминг разрешён в канале: {voice_channel.name}")
            else:
                if overwrite.stream:
                    overwrite.stream = False
                    await voice_channel.set_permissions(guild.default_role, overwrite=overwrite)
                    print(f"🚫 Стриминг запрещён в канале: {voice_channel.name}")

            # Проверяем участников на нарушение использования камеры/стрима
            for user in voice_channel.members:
                voice_state = user.voice
                if voice_state.self_video or voice_state.self_stream:
                    if not overwrite.stream:  # Стриминг запрещён
                        try:
                            # Перемещение пользователя в временный канал
                            temp_channel = guild.get_channel(607880556797100065)
                            if not temp_channel:
                                print("❌ Временный канал не найден.")
                                continue

                            # Перемещение пользователя в канал и обратно
                            await user.move_to(temp_channel)
                            print(f"🔄 {user.name} был перемещён в канал {temp_channel.name} для сброса.")
                            await asyncio.sleep(1)  # Небольшая задержка
                            await user.move_to(voice_channel)
                            print(f"✅ {user.name} возвращён в канал {voice_channel.name}.")
                        except disnake.Forbidden:
                            print(f"❌ Недостаточно прав для перемещения {user.name}.")
                        except disnake.HTTPException as e:
                            print(f"❌ Ошибка Discord API при перемещении {user.name}: {e}")
        else:
            print(f"Канал с ID {channel_id} не найден.")


# Запуск бота
bot.run(TOKEN)
