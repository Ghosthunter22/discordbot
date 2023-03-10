import discord
from discord.ext import commands
import asyncio
import os
import google.auth
from googleapiclient.discovery import build
import pytube
import ffmpeg

# Set up the YouTube API client
creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/youtube.force-ssl"])
youtube = build("youtube", "v3", credentials=creds)

# Define the bot's intents
intents = discord.Intents.default()
intents.members = True

# Set up the Discord bot client with the intents
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize the list of songs in the queue
queue = []

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='play')
async def play(ctx, *, query):
    # Get the voice channel the user is in
    voice_channel = ctx.author.voice.channel
    if not voice_channel:
        await ctx.send("You must be in a voice channel to use this command.")
        return

    # Connect to the voice channel
    voice_client = await voice_channel.connect()

    # Search for videos matching the query on YouTube
    video_ids = search_videos(query)

    # If no videos are found, send an error message
    if not video_ids:
        await ctx.send(f"No videos found for '{query}'.")
        await voice_client.disconnect()
        return

    # Download the audio from the first video in the search results
    audio_file = download_audio(video_ids[0])

    # Add the song to the queue
    queue.append((query, audio_file))

    # If this is the only song in the queue, start playing it
    if len(queue) == 1:
        play_next_song(voice_client, ctx)

    # Send a message confirming that the song has been added to the queue
    await ctx.send(f"'{query}' has been added to the queue.")

@bot.command(name='queue')
async def show_queue(ctx):
    # If the queue is empty, send a message saying so
    if len(queue) == 0:
        await ctx.send("The queue is currently empty.")
        return

    # Otherwise, send a message listing the songs in the queue
    queue_message = "Current queue:\n"
    for i, song in enumerate(queue):
        queue_message += f"{i+1}. {song[0]}\n"
    await ctx.send(queue_message)

@bot.command(name='skip')
async def skip_song(ctx):
    # If the queue is empty, send an error message
    if len(queue) == 0:
        await ctx.send("The queue is currently empty.")
        return

    # Get the voice client and stop the currently playing song
    voice_client = ctx.voice_client
    voice_client.stop()

    # Send a message indicating that the current song has been skipped
    skipped_song = queue.pop(0)
    await ctx.send(f"'{skipped_song[0]}' has been skipped.")

    # If there are more songs in the queue, start playing the next one
    if len(queue) > 0:
        play_next_song(voice_client, ctx)

@bot.command(name='stop')
async def stop_music(ctx):
    # Use the global keyword to modify the global variable
    global queue

    # If the queue is empty, send an error message
    if len(queue) == 0:
        await ctx.send("The queue is currently empty.")
        return

    # Clear the queue and stop playback
    queue = []
    voice_client = ctx.voice_client
    voice_client.stop()

    # Disconnect from the voice channel
    await voice_client.disconnect()
