import discord
from discord.ext import tasks
from discord import Permissions
from config import TOKEN  # import TOKEN from config.py

# server ID and voice channel ID, to observe
GUILD_ID = 607877371416150041  # ID вашего сервера
VOICE_CHANNEL_IDS = [690479552056786954]  # ID голосовых каналов (Бесконечное Цукуёми)

# max amount participants to allow using camera and streaming
MAX_PARTICIPANTS = 4

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
            # Get the number of participants
            participant_count = len(voice_channel.members)
            print(f"Channel {voice_channel.name}: {participant_count} participants")

            # Update permission according to the number of participants
            overwrite = voice_channel.overwrites_for(guild.default_role)
            if participant_count < MAX_PARTICIPANTS:
                if not overwrite.stream:  # Check if streaming allowed
                    overwrite.stream = True  # Allow streaming
                    await voice_channel.set_permissions(guild.default_role, overwrite=overwrite)
                    print(f"Permission is on for voice channel: {voice_channel.name}")
            else:
                if overwrite.stream:  # If the stream was allowed, turn it off
                    overwrite.stream = False
                    await voice_channel.set_permissions(guild.default_role, overwrite=overwrite)
                    print(f"Permission is off for voice channel: {voice_channel.name}")

            # Check participants for camera/stream violations
            for user in voice_channel.members:
                voice_state = user.voice  # Get the VoiceState of the user
                if voice_state.self_video or voice_state.self_stream:  # If user has camera or stream on
                    if not overwrite.stream:  # If streaming is not allowed
                        try:
                            # Get the temporary channel by ID
                            temp_channel = discord.utils.get(guild.voice_channels, id=607880556797100065)
                            if not temp_channel:
                                print("Channel with ID 607880556797100065 is not found.")
                                return

                            # Move user to the specified channel and back
                            await user.move_to(temp_channel)
                            print(f"{user.name} was moved to the channel {temp_channel.name} to reset.")
                            await user.move_to(voice_channel)
                            print(f"{user.name} was moved back to the channel {voice_channel.name}.")
                        except discord.Forbidden:
                            print(f"Not enough permissions to move {user.name}.")
                        except discord.HTTPException as e:
                            print(f"Discord API error: {e}")
        else:
            print(f"Channel with ID {channel_id} is not found")


client.run(TOKEN)
