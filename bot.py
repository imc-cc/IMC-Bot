# bot.py
import discord
import os
import time
import random
import sqlite3
import math
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
  money REAL NOT NULL,
  interestRate REAL NOT NULL,
  maxWithdraw INTEGER NOT NULL,
  maxDeposit INTEGER NOT NULL,
  maxTransfer INTEGER NOT NULL,
  creditScore INTEGER NOT NULL,
  amountWithdrew INTEGER NOT NULL,
  amountDeposited INTEGER NOT NULL,
  amountTransferred INTEGER NOT NULL
);
"""
execute_query(connection, create_accounts_table)

create_loans_table = """
CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    accountName TEXT NOT NULL,
    interestRate REAL NOT NULL,
    originalAmount INTEGER NOT NULL,
    amountRemaining REAL NOT NULL,
    discordID INTEGER NOT NULL,
    payPercent REAL NOT NULL,
    lateFee INTEGER NOT NULL,
    paid INTEGER NOT NULL
);
"""
execute_query(connection, create_loans_table)

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

#List of Administrators
ADMINS = os.getenv("ADMINS")
       
#endregion

#region Util Functions

def execute_query_many(connection, queries):
    cursor = connection.cursor()
    for query in queries:
        try:
            cursor.execute(query)
            connection.commit()
            print("Query of many executed successfully")
        except Error as e:
            print(f"The error '{e}' occurred")

#endregion 

#region Commands

#region Utilities

@bot.command(name='closeDoor', description='Stops the bot')
async def stopCommand(message):
    if str(message.author.id) not in ADMINS:
        await message.reply("You lack the permissions to run that command")
        return
    
    await message.reply("Stopping")
    
    quit()

#endregion

#region Accounts

#region Create Account Command
@bot.command(name='createAccount', description='creates an account')
async def createAccount(message, name: str = commands.parameter(description="Name for account"), password: str = commands.parameter(description="Password for account"), type: str = commands.parameter(description="Type of account to create")):

    checkLogin = f"""
    SELECT *
    FROM accounts 
    WHERE name = '{name}'
    """
    check = execute_read_query(connection, checkLogin)
    print(str(check))
    if check != []: 
        await message.reply("Account name is taken. Try again with a new name")
        return

    if type not in accountTypes:
        await message.reply("Account must be one of the following types: " + str(accountTypes).replace("[","").replace("]","").replace(",",""))
        return
    
    if type == "Checking":
        interestRate = 0.02
        maxWithdraw = 1024
        maxDeposit = 1024
        maxTransfer = 1024
    elif type == "Savings":
        interestRate = 0.04
        maxWithdraw = 512
        maxDeposit = 512
        maxTransfer = 512
    elif type == "Business":
        interestRate = 0.02
        maxWithdraw = 2048
        maxDeposit = 2048
        maxTransfer = 2048
    elif type == "Government":
        interestRate = 0.02
        maxWithdraw = 3072
        maxDeposit = 3072
        maxTransfer = 3072
    
    create_account= f"""
        INSERT INTO 
            accounts (name, password, type, money, interestRate, maxWithdraw, maxDeposit, maxTransfer, creditScore, amountWithdrew, amountDeposited, amountTransferred)
        VALUES
            ('{name}', '{password}', '{type}', 0, {interestRate}, {maxWithdraw}, {maxDeposit}, {maxTransfer}, 3, 0, 0, 0);"""
    
    channel = await bot.fetch_channel(logID)
    logMessage = await channel.send(f'{message.author.name} would like to open a {type} account with name {name} and password {password}')
    await logMessage.add_reaction('✅')
    await logMessage.add_reaction('❌')
    
    pendingQueries.append({
        "type": "single",
        "query":create_account,
        "id": logMessage.id,
        "msg": message,
        "successMessage": 'Account Created!',
        "denyMessage": 'Account creation denied. Message bank staff for more details. Sorry for the inconvenience!'
    })
    
    await message.reply(f'Pending...')

@createAccount.error
async def createAccount_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("All arguments not provided, try running the help command")
#endregion

#region Delete Account Command
@bot.command(name='deleteAccount', description='deletes an account')
async def deleteAccount(message, name: str = commands.parameter(description="Name of account"), password: str = commands.parameter(description="Password of account"), reason: str = commands.parameter(description="Why you want to delete it")):
    
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
        "type": "single",
        "query":delete_account,
        "id": logMessage.id,
        "msg": message,
        "successMessage": f'Account Deleted',
        "denyMessage": 'Account deletion denied. Message bank staff for more details. Sorry for the inconvenience!'
    })
    
    await message.reply(f'Pending...')

@deleteAccount.error
async def deleteAccount_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("All arguments not provided, try running the help command")
#endregion

#region Balance Command
@bot.command(name='bal', description='Finds the balance of an account')
async def accountBalance(message,name: str = commands.parameter(description="Name of account"),password: str = commands.parameter(description="Password of account")):
    
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
    
    balance_Query = f"""
    SELECT money
    FROM accounts
    WHERE password = '{password}' AND name = '{name}'
    """
    balance = execute_read_query(connection, balance_Query)
    
    embedVar = discord.Embed(title=f"{name}", color=0xF5C16A)
    embedVar.add_field(name="Balance", value=f"{ str(balance).replace("[(","").replace(",)]","") } IMC Denars")
    
    loan_Query = f"""
    SELECT id
    FROM loans
    WHERE accountName = '{name}'
    """
    loans = execute_read_query(connection, loan_Query)
    loanString = ""
    for i in loans:
        id = str(i).replace("(","").replace(",)","")
        
        amountRemaining_Query = execute_read_query(connection, f"SELECT amountRemaining FROM loans WHERE id = {id}")
        
        loanString += "ID: " + id + ";  Amount Remaining: " + str(amountRemaining_Query).replace("[(","").replace(",)]","") + " IMC Denars\n"
    
    if loanString != "":
        embedVar.add_field(name="Loans", value=f"{str(loanString)}", inline=False)
    
    await message.reply(embed=embedVar)

@accountBalance.error
async def bal_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("All arguments not provided, try running the help command")
#endregion

#endregion

#region Account Data

#region Deposit Command
@bot.command(name='deposit', description="Deposit money into your account")
async def depositCommand(message, name: str = commands.parameter(description="Name of account"), password: str = commands.parameter(description="Password of account"), amount: str = commands.parameter(description="Amount to deposit"), atmID: str = commands.parameter(description="ID of where you are depositing it")):
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
        await channel.send(f'{message.author.name} deposited {amount} IMC Denars into account \'{name}\' with password \'{password}\' into ATM with ID {atmID}.')
        await message.reply("Deposit Completed")
    else:
        logMessage = await channel.send(f'{message.author.name} would like to deposit {amount} IMC Denars into account \'{name}\' with password \'{password}\' into ATM with ID {atmID}.')
        await logMessage.add_reaction('✅')
        await logMessage.add_reaction('❌')
        
        pendingQueries.append({
            "type": "single",
            "query":deposit_query,
            "id": logMessage.id,
            "msg": message,
            "successMessage": f'Deposit Completed',
            "denyMessage": 'Deposit denied. Message bank staff for more details. Sorry for the inconvenience!'
        })
        
        await message.reply("Pending...")

@depositCommand.error
async def deposit_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("All arguments not provided, try running the help command")
#endregion

#region Withdraw Command
@bot.command(name='withdraw', description="Withdraw money from your account")
async def withdrawCommand(message, name: str = commands.parameter(description="Name of account"), password: str = commands.parameter(description="Password of account"), amount: str = commands.parameter(description="Amount to withdraw"), atmID: str = commands.parameter(description="ID of where you are depositing it")):
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
        await channel.send(f'{message.author.name} withdrew {amount} IMC Denars from account \'{name}\' with password \'{password}\' from ATM with ID {atmID}.')
        await message.reply("Withdraw Completed")
    else:
        logMessage = await channel.send(f'{message.author.name} would like to withdraw {amount} IMC Denars from account \'{name}\' with password \'{password}\' from ATM with ID {atmID}.')
        await logMessage.add_reaction('✅')
        await logMessage.add_reaction('❌')
        
        pendingQueries.append({
            "type": "single",
            "query":withdraw_query,
            "id": logMessage.id,
            "msg": message,
            "successMessage": f'Withdraw Completed',
            "denyMessage": 'Withdraw denied. Message bank staff for more details. The most likely reason is that you withdrew past your max withdraw amount. Sometimes we will allow this, but that is the exception not the rule. Sorry for the inconvenience!'
        })
        
        await message.reply("Pending...")

@withdrawCommand.error
async def withdraw_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("All arguments not provided, try running the help command")
#endregion

#region Transfer Command
@bot.command(name='transfer', description='Transfer money between accounts')
async def transferCommand(message, name: str = commands.parameter(description="Name of account"), password: str = commands.parameter(description="Password of account"), recipientName: str = commands.parameter(description="Name of recipient account"), amount: str = commands.parameter(description="Amount to transfer")):
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
    
    checkLogin = f"""
    SELECT *
    FROM accounts 
    WHERE name = '{recipientName}'
    """
    check = execute_read_query(connection, checkLogin)
    print(str(check))
    if check == []:
        await message.reply("Unable to find recipient. If you believe that you have the correct account name, contact bank staff.")
        return 
    
    maxTransfer = execute_read_query(connection, f"SELECT maxTransfer FROM accounts WHERE name = '{name}' AND password = '{password}'")
    maxTransfer = int(str(maxTransfer).replace("[(","").replace(",)]",""))
    
    money = execute_read_query(connection, f"SELECT money FROM accounts WHERE name = '{name}' AND password = '{password}'")
    money = float(str(money).replace("[(","").replace(",)]",""))
    
    moneyRecipient = execute_read_query(connection, f"SELECT money FROM accounts WHERE name = '{recipientName}'")
    moneyRecipient = float(str(moneyRecipient).replace("[(","").replace(",)]",""))
    
    amountTransferred = execute_read_query(connection, f"SELECT amountTransferred FROM accounts WHERE name = '{name}' AND password = '{password}'")
    amountTransferred = int(str(amountTransferred).replace("[(","").replace(",)]",""))
    
    if money < amount:
        await message.reply("You lack the funds to transfer that amount. You may want to look into taking a loan.")
        return
    
    sender_query = f"""
    UPDATE accounts SET money = {str(money-amount)}, amountTransferred = {str(amount+amountTransferred)} WHERE name = '{name}' AND password = '{password}';
    """
    recipient_query = f"""
    UPDATE accounts SET money = {str(moneyRecipient+amount)} WHERE name = '{recipientName}';
    """
    transfer_query=[sender_query,recipient_query]
    channel = await bot.fetch_channel(logID)
    
    if amount+amountTransferred <= maxTransfer:
        execute_query_many(connection, transfer_query)
        await channel.send(f'{message.author.name} transferred {amount} from account \'{name}\' to account \'{recipientName}\'')
        await message.reply("Transfer Completed")
    else:
        logMessage = await channel.send(f'{message.author.name} would like to transfer {amount} IMC Denars from account \'{name}\' to account \'{recipientName}\'')
        await logMessage.add_reaction('✅')
        await logMessage.add_reaction('❌')
        
        pendingQueries.append({
            "type": "many",
            "query":transfer_query,
            "id": logMessage.id,
            "msg": message,
            "successMessage": f'Transfer Completed',
            "denyMessage": 'Transfer denied. Message bank staff for more details. The most likely reason is that you transferred past your max transfer amount. Sometimes we will allow this, but that is the exception not the rule. Sorry for the inconvenience!'
        })
        
        await message.reply("Pending...")

@transferCommand.error
async def transfer_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("All arguments not provided, try running the help command")
#endregion

@bot.command(name='resetDailyMax', description='Resets the withdrew and deposited amount')
async def resetDailyMaxCommand(message):
    if str(message.author.id) not in ADMINS:
        await message.reply("You lack the permissions to run that command")
        return
    
    reset_query = """
    UPDATE accounts
    SET amountDeposited = 0,
        amountWithdrew = 0,
        amountTransferred = 0"""
        
    channel = await bot.fetch_channel(logID)
    logMessage = await channel.send(f'{message.author.name} would like to reset withdrew and deposited amounts')
    await logMessage.add_reaction('✅')
    await logMessage.add_reaction('❌')
        
    pendingQueries.append({
        "type": "single",
        "query":reset_query,
        "id": logMessage.id,
        "msg": message,
        "successMessage": f'Amounts Reset',
        "denyMessage": 'Someone declined the request.'
    })
    
    await message.reply("Pending...")

#region Account Edit Command
@bot.command(name='accountEdit', description='edits account data')
async def accountEdit(message, name: str = commands.parameter(description="Name of account"), dataToChange: str = commands.parameter(description="Name of data you want to change"), newData: str = commands.parameter(description="Data to change it to")):
    if str(message.author.id) not in ADMINS:
        await message.reply("You lack the permissions to run that command")
        return
    
    checkLogin = f"""
    SELECT *
    FROM accounts 
    WHERE name = '{name}'
    """
    check = execute_read_query(connection, checkLogin)
    print(str(check))
    if check == []: 
        await message.reply("Account not found")
        return
    
    update_query = f"""    UPDATE accounts SET {dataToChange} = {newData} WHERE name = '{name}'    """
    
    channel = await bot.fetch_channel(logID)
    logMessage = await channel.send(f'{message.author.name} would like to edit the data of account {name}. They wish to change data of {dataToChange} to {newData}')
    await logMessage.add_reaction('✅')
    await logMessage.add_reaction('❌')
        
    pendingQueries.append({
        "type": "single",
        "query":update_query,
        "id": logMessage.id,
        "msg": message,
        "successMessage": f'Update Completed',
        "denyMessage": 'Update Denied.'
    })
    
    await message.reply("Pending...")

@accountEdit.error
async def accountEdit_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("All arguments not provided, try running the help command")
#endregion

#endregion

#region Gambling

#region Dice Roll Command
@bot.command(name='dice', description='gamble on a dice roll')
async def diceRoll(message, name: str = commands.parameter(description="Name of account"), password: str = commands.parameter(description="Password of account"), guess: str = commands.parameter(description="Which number you would like to bet on"), betAmount: str = commands.parameter(description="How much you would like to bet")):
    
    try:
        guess = int(guess)
    except:
        await message.reply("Guess must be an integer")
        return
        
    try:
        betAmount = int(betAmount)
    except:
        await message.reply("Bet amount must be an integer")
        return
    
    if guess not in range(1,7):
        await message.reply("Guess must be a number in the range [1,6]")
        return
    
    checkLogin = f"""
    SELECT *
    FROM accounts 
    WHERE name = '{name}'"""
    
    check = execute_read_query(connection, checkLogin)
    if check == []: 
        await message.reply("Account not found")
        return
    
    money = execute_read_query(connection, f"SELECT money FROM accounts WHERE name = '{name}' AND password = '{password}'")
    money = float(str(money).replace("[(","").replace(",)]",""))
    
    print(str(money))
    
    if money < betAmount:
        await message.reply("You lack the funds for that transaction.")
        return
    
    roll = random.randint(1,6)
    print(str(roll))
    
    channel = await bot.fetch_channel(logID)
    
    if roll == guess:
        money += betAmount*2
        await message.reply(f"The dice rolled {str(roll)}. You win! Your money got tripled! You now have {str(money)} IMC Denars")
        await channel.send(f"{message.author.name} won {str(betAmount)} on a dice roll! They now have {str(money)} IMC Denars")
    else:
        money -= betAmount
        await message.reply(f"The dice rolled {str(roll)}. You lost {str(betAmount)} IMC Denars...")
        await channel.send(f"{message.author.name} lost {str(betAmount)} on a dice roll! They now have {str(money)} IMC Denars")
        
    gamble_query = f"""
    UPDATE accounts
    SET money = {str(money)}
    WHERE name = '{name}' AND password = '{password}'
    """
    
    execute_query(connection, gamble_query)

@diceRoll.error
async def diceRoll_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("All arguments not provided, try running the help command")
#endregion

#endregion

#region Loans

#region Loan Apply
@bot.command(name='loanApply', description='Apply for a loan')
async def loanApply(message, 
                    name: str = commands.parameter(description="Name of account"), 
                    password: str = commands.parameter(description="Password of account"), 
                    amount: str = commands.parameter(description="Amount you would like to take out a loan for"), 
                    reason: str = commands.parameter(description="Why you need the loan")):
    
    try:
        amount = int(amount)
        if amount <= 0:
            await message.reply("Amount must be a positive integer")
            return
    except:
        await message.reply("Amount must be a positive integer")
        return
    
    checkLogin = f"""
    SELECT *
    FROM accounts 
    WHERE name = '{name}' AND password = '{password}'"""
    
    check = execute_read_query(connection, checkLogin)
    if check == []: 
        await message.reply("Account not found")
        return
    
    creditScore = execute_read_query(connection, f"SELECT creditScore FROM accounts WHERE name = '{name}' AND password = '{password}'")
    creditScore = int(str(creditScore).replace("[(","").replace(",)]",""))
    
    payPercent = 0;
    lateFee = 0;
    interestRate = 0;
    if creditScore == 0:
        interestRate = 0.2
        payPercent = 0.15
        lateFee = math.floor(amount*0.2)
    elif creditScore == 1:
        interestRate = 0.15
        payPercent = 0.11
        lateFee = math.floor(amount*0.15)
    elif creditScore == 2:
        interestRate = 0.125
        payPercent = 0.09
        lateFee = math.floor(amount*0.125)
    elif creditScore == 3:
        interestRate = 0.1
        payPercent = 0.075
        lateFee = math.floor(amount*0.1)
    elif creditScore == 4:
        interestRate = 0.08
        payPercent = 0.06
        lateFee = math.floor(amount*0.08)
    elif creditScore == 5:
        interestRate = 0.07
        payPercent = 0.05
        lateFee = math.floor(amount*0.07)
    elif creditScore == 6:
        interestRate = 0.05
        payPercent = 0.05
        lateFee = math.floor(amount*0.05)
        
    createLoan_query= f"""
    INSERT INTO 
        loans (accountName, interestRate, originalAmount, amountRemaining, discordID, payPercent, lateFee, paid)
    VALUES
        ('{name}', {str(interestRate)}, {str(amount)}, {str(amount)}, {message.author.id}, {str(payPercent)}, {str(lateFee)}, 0);"""   
    
    money = execute_read_query(connection, f"SELECT money FROM accounts WHERE name = '{name}' AND password = '{password}'")
    money = float(str(money).replace("[(","").replace(",)]",""))
        
    sendMoney_query= f"""
    UPDATE accounts SET money = {str(money+amount)} WHERE name = '{name}' AND password = '{password}';
    """
    
    money = execute_read_query(connection, f"SELECT money FROM accounts WHERE name = 'IMC'")
    money = float(str(money).replace("[(","").replace(",)]",""))
    
    IMCMoney_query= f"""
    UPDATE accounts SET money = {str(money-amount)} WHERE name = 'IMC';
    """
        
    loan_query = [createLoan_query, sendMoney_query, IMCMoney_query]
    
    channel = await bot.fetch_channel(logID)
    logMessage = await channel.send(f'{message.author.name} would like to get a loan on an account with name {name} and password {password} for {str(amount)} IMC Denars. They have a credit score of {str(creditScore)}. They want this loan because {reason}')
    await logMessage.add_reaction('✅')
    await logMessage.add_reaction('❌')
    
    pendingQueries.append({
        "type": "many",
        "query":loan_query,
        "id": logMessage.id,
        "msg": message,
        "successMessage": 'Loan Approved!',
        "denyMessage": 'Loan denied. Message bank staff for more details. Sorry for the inconvenience!'
    })
    
    await message.reply("Awaiting approval")

@loanApply.error
async def loanApply_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("All arguments not provided, try running the help command")
#endregion

#region Loan Negotiate
@bot.command(name='loanNegotiate', description='Apply for a loan where you negotiate the terms')
async def loanNegotiate(message, 
                    name: str = commands.parameter(description="Name of account"), 
                    password: str = commands.parameter(description="Password of account"), 
                    amount: str = commands.parameter(description="Amount you would like to take out a loan for"), 
                    interestRate: str = commands.parameter(description="Starting offer interest rate"), 
                    payPercent: str = commands.parameter(description="Starting offer minimum monthly payment"), 
                    lateFee: str = commands.parameter(description="Starting offer late fee"), 
                    reason: str = commands.parameter(description="Why you need a loan")):
    
    try:
        amount = int(amount)
        if amount <= 0:
            await message.reply("Amount must be a positive integer")
            return
    except:
        await message.reply("Amount must be a positive integer")
        return
    
    try:
        interestRate = float(interestRate)
        if interestRate <= 0:
            await message.reply("Interest Rate must be a positive decimal value")
            return
    except:
        await message.reply("Interest Rate must be a positive decimal value")
        return
    
    try:
        payPercent = float(payPercent)
        if payPercent <= 0:
            await message.reply("Pay Percent must be a positive decimal value")
            return
    except:
        await message.reply("Pay Percent must be a positive decimal value")
        return
    
    try:
        lateFee = int(lateFee)
        if lateFee <= 0:
            await message.reply("Late Fee must be a positive integer")
            return
    except:
        await message.reply("Late Fee must be a positive integer")
        return
    
    checkLogin = f"""
    SELECT *
    FROM accounts 
    WHERE name = '{name}' AND password = '{password}'"""
    
    check = execute_read_query(connection, checkLogin)
    if check == []: 
        await message.reply("Account not found")
        return
    
    creditScore = execute_read_query(connection, f"SELECT creditScore FROM accounts WHERE name = '{name}' AND password = '{password}'")
    creditScore = int(str(creditScore).replace("[(","").replace(",)]",""))
        
    createLoan_query= f"""
    INSERT INTO 
        loans (accountName, interestRate, originalAmount, amountRemaining, discordID, payPercent, lateFee, paid)
    VALUES
        ('{name}', {str(interestRate)}, {str(amount)}, {str(amount)}, {message.author.id}, {str(payPercent)}, {str(lateFee)}, 0);""" 
        
    money = execute_read_query(connection, f"SELECT money FROM accounts WHERE name = '{name}' AND password = '{password}'")
    money = float(str(money).replace("[(","").replace(",)]",""))
        
    sendMoney_query= f"""
    UPDATE accounts SET money = {str(money+amount)} WHERE name = '{name}' AND password = '{password}';
    """
    
    money = execute_read_query(connection, f"SELECT money FROM accounts WHERE name = 'IMC'")
    money = float(str(money).replace("[(","").replace(",)]",""))
    
    IMCMoney_query= f"""
    UPDATE accounts SET money = {str(money-amount)} WHERE name = 'IMC';
    """
        
    loan_query = [createLoan_query, sendMoney_query, IMCMoney_query]
        
    channel = await bot.fetch_channel(logID)
    logMessage = await channel.send(f'{message.author.name} would like to **negotiate** a loan on an account with name {name} and password {password} for {str(amount)} IMC Denars. They have a credit score of {str(creditScore)}. They want an interest rate of {str(interestRate)}, a monthly pay percent of {str(payPercent)}, and a late fee of {str(lateFee)}. The reason they want the loan is \'{reason}\'')
    await logMessage.add_reaction('✅')
    await logMessage.add_reaction('❌')
    
    pendingQueries.append({
        "type": "many",
        "query":loan_query,
        "id": logMessage.id,
        "msg": message,
        "successMessage": 'Loan Approved!',
        "denyMessage": 'Loan denied. Message bank staff for more details. Sorry for the inconvenience!'
    })
    
    await message.reply("Finding Bank Staff. Someone will message you to negotiate shortly")

@loanNegotiate.error
async def loanNegotiate_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("All arguments not provided, try running the help command")
#endregion

#region Loan Delete
@bot.command(name='loanDelete', description='Delete a loan')
async def loanDelete(message, 
                        id: str = commands.parameter(description="ID of loan"), 
                        reason: str = commands.parameter(description="Reason for deleting loan")):
    
    if str(message.author.id) not in ADMINS:
        await message.reply("You lack the permissions to run that command")
        return
    
    checkLoan = f"""
    SELECT *
    FROM loans
    WHERE id = {id}
    """
    check = execute_read_query(connection, checkLoan)
    print(str(check))
    if check == []:
        await message.reply("Unable to find loan.")
        return
    
    delete_loan= f"""
    DELETE 
    FROM loans
    WHERE id = {id}
    """
    
    channel = await bot.fetch_channel(logID)
    logMessage = await channel.send(f'{message.author.name} would like to delete loan ID {id}. Their reason is \"{reason}\"')
    await logMessage.add_reaction('✅')
    await logMessage.add_reaction('❌')
    
    pendingQueries.append({
        "type": "single",
        "query":delete_loan,
        "id": logMessage.id,
        "msg": message,
        "successMessage": f'Loan Deleted',
        "denyMessage": 'Loan deletion denied. Message bank staff for more details. Sorry for the inconvenience!'
    })
    
    await message.reply(f'Pending...')

@loanDelete.error
async def loanDelete_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("All arguments not provided, try running the help command")
#endregion

#region Loan Pay
@bot.command(name='payLoan', description='Pays back part of your loan')
async def payLoan(message,
                    name: str = commands.parameter(description="Name of account"),
                    password: str = commands.parameter(description="Password of account"),
                    id: str = commands.parameter(description="ID of loan you wish to pay"),
                    amount: str = commands.parameter(description="Amount you would like to pay back")):
    
    try: int(id)
    except: 
        await message.reply("ID must be an integer")
        return
    
    try: amount = int(amount)
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
    
    checkLoan = f"""
    SELECT amountRemaining
    FROM loans 
    WHERE id = {id} AND accountName = '{name}'
    """
    check = execute_read_query(connection, checkLoan)
    print(str(check))
    if check == []:
        await message.reply("Unable to find loan or loan is not on this account")
        return
    
    amountRemaining = float(str(check).replace("[(","").replace(",)]",""))
    
    if amount > amountRemaining:
        await message.reply("You cannot pay back more money than is remaining on the loan")
        return
    
    payPercent = execute_read_query(connection, f"SELECT payPercent FROM loans WHERE id = {id} AND accountName = '{name}'")
    payPercent = float(str(payPercent).replace("[(","").replace(",)]",""))
    
    if (amount < amountRemaining*payPercent) and (amountRemaining-amount >= amountRemaining*payPercent):
        await message.reply("You cannot pay less than your minimum pay percent")
        return
    
    money = execute_read_query(connection, f"SELECT money FROM accounts WHERE name = '{name}' AND password = '{password}'")
    money = float(str(money).replace("[(","").replace(",)]",""))
    
    IMCmoney = execute_read_query(connection, f"SELECT money FROM accounts WHERE name = 'IMC'")
    IMCmoney = float(str(IMCmoney).replace("[(","").replace(",)]",""))
    
    pay_Query=f"UPDATE accounts SET money = {str(money-amount)} WHERE name = '{name}' AND password = '{password}';"
    recieve_Query=f"UPDATE accounts SET money = {str(IMCmoney+amount)} WHERE name = 'IMC';"
    loan_Query=f"UPDATE loans SET amountRemaining = {str(amountRemaining-amount)}, paid = 1 WHERE id = {id} AND accountName = '{name}';"
    
    queries = [pay_Query,recieve_Query,loan_Query]
    execute_query_many(connection,queries)
    
    await message.reply("Loan Payment Completed")
    
    if amountRemaining-amount < 1:
        execute_query(connection, f"DELETE FROM loans WHERE id = {id}")
        await message.reply("Loan fully paid!")

@payLoan.error
async def payLoan_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("All arguments not provided, try running the help command")
#endregion

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
                if i["type"]=="many":
                    execute_query_many(connection, i["query"])
                else:
                    execute_query(connection, i["query"])
                await i["msg"].reply(i["successMessage"])
                pendingQueries.remove(i)
            elif reaction.emoji == '❌':
                await i["msg"].reply(i["denyMessage"])
                pendingQueries.remove(i)
            
            return
           
#endregion

bot.run(TOKEN)