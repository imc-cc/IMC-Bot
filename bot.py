# bot.py
import discord
import os
import time
import sqlite3
from sqlite3 import Error
from discord.ext import commands
from dotenv import load_dotenv

#region Setup

#region Connect to Discord
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.all()
intents.message_content = True

prefix = '-'

bot = commands.Bot(command_prefix=prefix, intents=intents)
#endregion

#region Connect to database

def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        print("Connection to SQLite DB Successful")
    except Error as e:
        print(f"The error '{e}' occurred")
        
    return connection

connection = create_connection(os.getenv('DB_PATH'))

#endregion

def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print("Query executed successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

#region setup tables

create_accounts_table = """
CREATE TABLE IF NOT EXISTS accounts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  password TEXT NOT NULL,
  type TEXT NOT NULL,
  level INTEGER NOT NULL,
  money REAL NOT NULL,
  interestRate REAL NOT NULL,
  maxWithdraw INTEGER NOT NULL,
  maxDeposit INTEGER NOT NULL,
  active INTEGER NOT NULL,
  creditScore INTEGER NOT NULL
);
"""
execute_query(connection, create_accounts_table)

#endregion

def execute_read_query(connection, query):
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as e:
        print(f"The error '{e}' occurred")
        
#endregion

#region Commands

#region Utilities
@bot.command(name='closeDoor', description='Stops the bot')
async def stopCommand(message):
    await message.reply("Stopping")
    
    quit()

#endregion

#region Accounts

@bot.command(name='createAccount', description='creates an account')
async def createAccount(message, password, name, type):
    create_account= f"""
        INSERT INTO 
            accounts (name, password, type, level, money, interestRate, maxWithdraw, maxDeposit, active, creditScore)
        VALUES
            ('{name}', '{password}', '{type}', 3, 0, 0.04, 1024, 1024, 1, 3);
    """
    
    execute_query(connection, create_account)
    
    await message.reply(f'{type} Account Created with name {name}, password {password}')
    

#endregion

#endregion

bot.run(TOKEN)