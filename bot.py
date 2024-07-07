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
  name TEXT NOT NULL,
  password TEXT NOT NULL,
  type TEXT NOT NULL,
  level INTEGER NOT NULL,
  money REAL NOT NULL,
  interestRate REAL NOT NULL,
  maxWithdraw INTEGER NOT NULL,
  maxDeposit INTEGER NOT NULL,
  active INTEGER NOT NULL,
  creditScore INTEGER NOT NULL,
  amountWithdrew INTEGER NOT NULL,
  amountDeposited INTEGER NOT NULL
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
     
logID = os.getenv("LOG_CHANNEL_ID")

#Create pending queries list
pendingQueries = [] 
       
#Account types
accountTypes = ["Checking", "Savings", "Government", "Business"]
       
#endregion

#region Util Functions


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
async def createAccount(message, name, password, type):

    if type not in accountTypes:
        await message.reply("Account must be one of the following types: " + str(accountTypes).replace("[","").replace("]","").replace(",",""))
        return
    
    if type == "Checking":
        interestRate = 0.02
        maxWithdraw = 1024
        maxDeposit = 1024
    elif type == "Savings":
        interestRate = 0.04
        maxWithdraw = 512
        maxDeposit = 512
    elif type == "Business":
        interestRate = 0.02
        maxWithdraw = 2048
        maxDeposit = 2048
    elif type == "Government":
        interestRate = 0.02
        maxWithdraw = 3072
        maxDeposit = 3072
    
    create_account= f"""
        INSERT INTO 
            accounts (name, password, type, level, money, interestRate, maxWithdraw, maxDeposit, active, creditScore, amountWithdrew, amountDeposited)
        VALUES
            ('{name}', '{password}', '{type}', 3, 0, {interestRate}, {maxWithdraw}, {maxDeposit}, 1, 3, 0, 0);"""
    
    channel = await bot.fetch_channel(logID)
    logMessage = await channel.send(f'{message.author.name} would like to open a {type} account with name {name} and password {password}')
    await logMessage.add_reaction('✅')
    await logMessage.add_reaction('❌')
    
    pendingQueries.append({
        "query":create_account,
        "id": logMessage.id,
        "msg": message,
        "successMessage": 'Account Created!',
        "denyMessage": 'Account creation denied. Message bank staff for more details. Sorry for the inconvenience!'
    })
    
    await message.reply(f'Pending...')

@bot.command(name='deleteAccount', description='deletes an account')
async def deleteAccount(message, name, password, reason):
    
    delete_account= f"""
    DELETE 
    FROM accounts
    WHERE password = '{password}' AND name = '{name}'
    """
    
    channel = await bot.fetch_channel(logID)
    logMessage = await channel.send(f'{message.author.name} would like to delete account \'{name}\' with password {password}. Their reason is \"{reason}\"')
    await logMessage.add_reaction('✅')
    await logMessage.add_reaction('❌')
    
    pendingQueries.append({
        "query":delete_account,
        "id": logMessage.id,
        "msg": message,
        "successMessage": f'Account Deleted',
        "denyMessage": 'Account deletion denied. Message bank staff for more details. Sorry for the inconvenience!'
    })
    
    await message.reply(f'Pending...')

@bot.command(name='bal', description='Finds the balance of an account')
async def accountBalance(message,name,password):
    
    balanceQuery = f"""
    SELECT money
    FROM accounts
    WHERE password = '{password}' AND name = '{name}'
    
    """
    
    balance = execute_read_query(connection, balanceQuery)
    await message.reply("Your balance is: " + str(balance).replace("[(","").replace(",)]","") + " IMC Denars")
#endregion

#region Holdings

@bot.command(name='deposit', description="Deposit money into your account")
async def depositCommand(message, name, password, amount):
    try:
        amount = int(amount)
    except:
        await message.reply("Amount must be an integer")
        return
        
    checkLogin = f"""
    SELECT *
    FROM accounts 
    WHERE name = '{name}' AND password = '{password}'
    """
    check = execute_read_query(connection, checkLogin)
    print(str(check))
    if check == []:
        await message.reply("Incorrect name or password. If you believe that you have the correct name and password, contact bank staff.")
        return
    
    maxDeposit = execute_read_query(connection, f"SELECT maxDeposit FROM accounts WHERE name = '{name}' AND password = '{password}'")
    maxDeposit = int(str(maxDeposit).replace("[(","").replace(",)]",""))
    
    money = execute_read_query(connection, f"SELECT money FROM accounts WHERE name = '{name}' AND password = '{password}'")
    money = float(str(money).replace("[(","").replace(",)]",""))
    
    amountDeposited = execute_read_query(connection, f"SELECT amountDeposited FROM accounts WHERE name = '{name}' AND password = '{password}'")
    amountDeposited = int(str(amountDeposited).replace("[(","").replace(",)]",""))
    
    deposit_query = f"""
    UPDATE accounts
    SET money = {str(money+amount)},
        amountDeposited = {str(amount+amountDeposited)}
    WHERE name = '{name}' AND password = '{password}'
    
    """
    channel = await bot.fetch_channel(logID)
    
    if amount+amountDeposited <= maxDeposit:
        execute_query(connection, deposit_query)
        await channel.send(f'{message.author.name} deposited {amount} IMC Denars into account \'{name}\' with password \'{password}.\'')
        await message.reply("Deposit Completed")
    else:
        logMessage = await channel.send(f'{message.author.name} would like to deposit {amount} IMC Denars into account \'{name}\' with password \'{password}\'.')
        await logMessage.add_reaction('✅')
        await logMessage.add_reaction('❌')
        
        pendingQueries.append({
            "query":deposit_query,
            "id": logMessage.id,
            "msg": message,
            "successMessage": f'Deposit Completed',
            "denyMessage": 'Deposit denied. Message bank staff for more details. Sorry for the inconvenience!'
        })
        
        await message.reply("Pending...")

@bot.command(name='withdraw', description="Withdraw money from your account")
async def withdrawCommand(message, name, password, amount):
    try:
        amount = int(amount)
    except:
        await message.reply("Amount must be an integer")
        return
        
    checkLogin = f"""
    SELECT *
    FROM accounts 
    WHERE name = '{name}' AND password = '{password}'
    """
    check = execute_read_query(connection, checkLogin)
    print(str(check))
    if check == []:
        await message.reply("Incorrect name or password. If you believe that you have the correct name and password, contact bank staff.")
        return
    
    maxWithdraw = execute_read_query(connection, f"SELECT maxWithdraw FROM accounts WHERE name = '{name}' AND password = '{password}'")
    maxWithdraw = int(str(maxWithdraw).replace("[(","").replace(",)]",""))
    
    money = execute_read_query(connection, f"SELECT money FROM accounts WHERE name = '{name}' AND password = '{password}'")
    money = float(str(money).replace("[(","").replace(",)]",""))
    
    amountWithdrew = execute_read_query(connection, f"SELECT amountWithdrew FROM accounts WHERE name = '{name}' AND password = '{password}'")
    amountWithdrew = int(str(amountWithdrew).replace("[(","").replace(",)]",""))
    
    if money < amount:
        await message.reply("You lack the funds to withdraw that amount. You may want to look into taking a loan.")
        return
    
    withdraw_query = f"""
    UPDATE accounts
    SET money = {str(money-amount)},
        amountWithdrew = {str(amount+amountWithdrew)}
    WHERE name = '{name}' AND password = '{password}'
    """
    channel = await bot.fetch_channel(logID)
    
    if amount+amountWithdrew <= maxWithdraw:
        execute_query(connection, withdraw_query)
        await channel.send(f'{message.author.name} withdrew {amount} IMC Denars from account \'{name}\' with password \'{password}.\'')
        await message.reply("Withdraw Completed")
    else:
        logMessage = await channel.send(f'{message.author.name} would like to withdraw {amount} IMC Denarsfrom account \'{name}\' with password \'{password}\'.')
        await logMessage.add_reaction('✅')
        await logMessage.add_reaction('❌')
        
        pendingQueries.append({
            "query":withdraw_query,
            "id": logMessage.id,
            "msg": message,
            "successMessage": f'Withdraw Completed',
            "denyMessage": 'Withdraw denied. Message bank staff for more details. The most likely reason is that you withdrew past your max withdraw amount. Sometimes we will allow this, but that is the exception not the rule. Sorry for the inconvenience!'
        })
        
        await message.reply("Pending...")

@bot.command(name='resetDailyMax', description='Resets the withdrew and deposited amount')
async def resetDailyMaxCommand(message):
    reset_query = """
    UPDATE accounts
    SET amountDeposited = 0,
        amountWithdrew = 0"""
        
    channel = await bot.fetch_channel(logID)
    logMessage = await channel.send(f'{message.author.name} would like to reset withdrew and deposited amounts')
    await logMessage.add_reaction('✅')
    await logMessage.add_reaction('❌')
        
    pendingQueries.append({
        "query":reset_query,
        "id": logMessage.id,
        "msg": message,
        "successMessage": f'Amounts Reset',
        "denyMessage": 'Someone declined the request.'
    })
    
    await message.reply("Pending...")

#endregion

#endregion

#region Events

@bot.event
async def on_reaction_add(reaction, user):
    if(user == bot.user):
        return
    
    for i in pendingQueries:
        if i["id"] == reaction.message.id:
            if reaction.emoji == '✅':
                execute_query(connection, i["query"])
                await i["msg"].reply(i["successMessage"])
                pendingQueries.remove(i)
            elif reaction.emoji == '❌':
                await i["msg"].reply(i["denyMessage"])
                pendingQueries.remove(i)
           
#endregion

bot.run(TOKEN)