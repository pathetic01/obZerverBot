import discord
from discord.ext import tasks
from discord import Permissions

# your BOT token
TOKEN = 'TOKEN'

# server ID and voice channel ID, to observe
GUILD_ID = 607871271416150123  # ID вашего сервера
VOICE_CHANNEL_IDS = [690479112056786123, 656951238131968023]  # ID голосовых каналов (Бесконечное Цук.; PornHub)

# max amount participants to allow using camera and streaming
MAX_PARTICIPANTS = 25

# settings for event
intents = discord.Intents.default()
intents.voice_states = True  # allow to observe voice channels
intents.guilds = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'Bot is running as {client.user}')
    monitor_channels.start()


@tasks.loop(seconds=10)  # check channel every 10 sec
async def monitor_channels():
    guild = discord.utils.get(client.guilds, id=GUILD_ID)
    if not guild:
        print("Server is not found")
        return

    for channel_id in VOICE_CHANNEL_IDS:
        voice_channel = discord.utils.get(guild.voice_channels, id=channel_id)
        if voice_channel:
            # get amount of participants
            participant_count = len(voice_channel.members)
            print(f"Channel {voice_channel.name}: {participant_count} participants")

            # update permission according to amount of participants
            overwrite = voice_channel.overwrites_for(guild.default_role)
            if participant_count < MAX_PARTICIPANTS:
                if not overwrite.stream:  # check if streaming allowed
                    overwrite.stream = True  # allow streaming
                    await voice_channel.set_permissions(guild.default_role, overwrite=overwrite)
                    print(f"Permission is on for voice channel: {voice_channel.name}")
            else:
                if overwrite.stream:  # If the stream was allowed, turn it off
                    overwrite.stream = False
                    await voice_channel.set_permissions(guild.default_role, overwrite=overwrite)
                    print(f"Permission is off for voice channel: {voice_channel.name}")
        else:
            print(f"Channel with ID {channel_id} is not found")


client.run(TOKEN)