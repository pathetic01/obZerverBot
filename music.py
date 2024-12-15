import disnake
from disnake.ext import commands
import yt_dlp
import asyncio
from disnake import FFmpegPCMAudio

# Настройки для youtube-dl и FFmpeg
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
    'executable': 'D:/PyProject/ffmpeg/bin/ffmpeg.exe'  # Путь к FFmpeg
}

YDL_OPTIONS = {"format": "bestaudio", "noplaylist": "True"}


def setup_music_commands(bot: commands.Bot):
    @bot.slash_command(name="play", description="Воспроизвести музыку по запросу")
    async def play(inter: disnake.ApplicationCommandInteraction, query: str):
        if not inter.author.voice:
            await inter.response.send_message("❌ Вы должны находиться в голосовом канале!")
            return

        voice_channel = inter.author.voice.channel

        # Подключаемся к голосовому каналу
        if not inter.guild.voice_client:
            await voice_channel.connect()
            await inter.response.send_message(f"🔊 Подключился к каналу {voice_channel.name}", ephemeral=True)
        else:
            await inter.response.defer()  # Отложить ответ, если команда требует времени

        # Загрузка информации о треке
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)["entries"][0]
                url = info["url"]
                title = info["title"]

                # Воспроизводим трек
                voice_client = inter.guild.voice_client
                if voice_client.is_playing():
                    await inter.followup.send(f"🎵 Трек добавлен в очередь: {title}")
                else:
                    voice_client.play(FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
                                      after=lambda e: print(f"FFmpeg завершён: {e}"))
                    await inter.followup.send(f"🎶 Сейчас играет: {title}")

            except Exception as e:
                await inter.followup.send(f"❌ Ошибка при воспроизведении музыки: {e}")

    @bot.slash_command(name="stop", description="Остановить воспроизведение музыки")
    async def stop(inter: disnake.ApplicationCommandInteraction):
        if inter.guild.voice_client:
            await inter.guild.voice_client.disconnect()
            await inter.response.send_message("⏹ Остановил музыку и вышел из канала.")
        else:
            await inter.response.send_message("❌ Бот не подключен к голосовому каналу.")