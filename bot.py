# bot.py
import discord
import os
import time
from discord.ext import commands
from dotenv import load_dotenv

#region Setup
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
intents.message_content = True

prefix = '-'

bot = commands.Bot(command_prefix=prefix, intents=intents)
#endregion

#region Commands

@bot.command(name='stop', description='Stops the bot')
async def stopCommand(message):
    await message.reply("Stopping")
    
    quit()

#endregion

bot.run(TOKEN)