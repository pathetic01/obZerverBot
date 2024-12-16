import disnake
import asyncio
from disnake.ext import commands, tasks
from config import TOKEN  # Import TOKEN from config.py
from music import setup_music_commands  # Import music functionality

# server ID and voice channel ID, to observe
GUILD_ID = 607877371416150041  # ID of your server
VOICE_CHANNEL_IDS = [690479552056786954]  # ID of voice channels to monitor
MAX_PARTICIPANTS = 25  # Maximum allowed participants in a voice channel. (25)

ALLOWED_CHANNEL_ID = 608659506922127420  # ID of the text channel for bot interactions

# Define intents to specify bot permissions
intents = disnake.Intents.all()

# Create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents, test_guilds=[GUILD_ID])  # test_guilds for faster command sync

# Monitoring status flag
monitoring_enabled = False

# Setup music commands
setup_music_commands(bot)

# Event triggered when the bot is ready
@bot.event
async def on_ready():
    print(f"✅ Bot is running as {bot.user}")


# /ping command to check if the bot is working
@bot.slash_command(name="ping", description="Check if the bot is working")
async def ping(inter: disnake.ApplicationCommandInteraction):
    if inter.channel.id != ALLOWED_CHANNEL_ID:
        return
    await inter.response.send_message("🏓 Pong!")


# /enable_monitor command to start monitoring voice channels
@bot.slash_command(name="enable_monitor", description="Enable participant monitoring")
async def enable_monitor(inter: disnake.ApplicationCommandInteraction):
    global monitoring_enabled
    if inter.channel.id != ALLOWED_CHANNEL_ID:
        return
    if not monitoring_enabled:
        monitoring_enabled = True
        monitor_channels.start()
        await inter.response.send_message("🔍 Participant monitoring enabled.")
    else:
        await inter.response.send_message("🔍 Monitoring is already enabled.")


# /disable_monitor command to stop monitoring voice channels
@bot.slash_command(name="disable_monitor", description="Disable participant monitoring")
async def disable_monitor(inter: disnake.ApplicationCommandInteraction):
    global monitoring_enabled
    if inter.channel.id != ALLOWED_CHANNEL_ID:  # Ensure the command is used in the allowed channel
        return
    if monitoring_enabled:                      # If monitoring is currently enabled
        monitoring_enabled = False
        monitor_channels.stop()                 # Stop the monitoring loop
        await inter.response.send_message("🛑 Participant monitoring disabled.")
    else:
        await inter.response.send_message("🛑 Monitoring is already disabled.")


# Loop to monitor voice channels
@tasks.loop(seconds=10)
async def monitor_channels():
    if not monitoring_enabled:  # Skip if monitoring is disabled
        return

    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("Server not found.")
        return

    for channel_id in VOICE_CHANNEL_IDS: # Iterate through monitored voice channels
        voice_channel = guild.get_channel(channel_id)
        if voice_channel:
            participant_count = len(voice_channel.members)
            print(f"Канал {voice_channel.name}: {participant_count} участников")

            overwrite = voice_channel.overwrites_for(guild.default_role)
            if participant_count < MAX_PARTICIPANTS:
                if not overwrite.stream:
                    overwrite.stream = True
                    await voice_channel.set_permissions(guild.default_role, overwrite=overwrite)
                    print(f"✅ Streaming allowed in channel: {voice_channel.name}")
            else:
                if overwrite.stream:
                    overwrite.stream = False
                    await voice_channel.set_permissions(guild.default_role, overwrite=overwrite)
                    print(f"🚫 Streaming disabled in channel: {voice_channel.name}")

            # Check if any participant violates the streaming rule
            for user in voice_channel.members:
                voice_state = user.voice
                if voice_state is None:  # Skip users without active voice state
                    continue

                if voice_state.self_video or voice_state.self_stream:  # If the user has camera or stream on
                    if not overwrite.stream:  # Streaming is disallowed
                        try:
                            # Get the temporary channel by ID
                            temp_channel = guild.get_channel(607880556797100065)
                            if not temp_channel:
                                print("❌ Temporary channel not found.")
                                continue

                            # Move the user to the temporary channel and back
                            await user.move_to(temp_channel)
                            print(f"🔄 {user.name} was moved to {temp_channel.name} for reset.")
                            await asyncio.sleep(1)  # Brief delay
                            await user.move_to(voice_channel)
                            print(f"✅ {user.name} was moved back to {voice_channel.name}.")
                        except disnake.Forbidden:
                            print(f"❌ Insufficient permissions to move {user.name}.")
                        except disnake.HTTPException as e:
                            print(f"❌ Discord API error while moving {user.name}: {e}")
        else:
            print(f"Channel with ID {channel_id} not found.")


# Run the bot
bot.run(TOKEN)
