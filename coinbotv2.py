#This supports the most recent discord.py library.
import discord
import asyncio
import requests
import feedparser
import datetime
import re
from decimal import Decimal
from password import KEY, IEX_TOKEN, CMK_TOKEN
from tabulate import tabulate
from discord.ext import commands
import json

#This is used for discord.py >= V1.0; python 3.5+;

'''
CoinBase: Crypto prices
CoinMarketCap: Other Crypto price
CryptoHistory: Crypto Charts
IEXPrice: Stock ticker price
StockCharts: Stock Charts
'''
description = '''Discord bot for fetching Crypto and Stock Prices in discord'''
bot = commands.Bot(command_prefix='[!,$]', description=description)

portfolio = {}

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.event
async def on_message(message):
    if message.content.lower().startswith(('!help')):
        await message.channel.trigger_typing()
        Help = discord.Embed(title="Help Menu", description="Commands")
        Help.add_field(name="!COIN_TICKER", value="Gets the latest cryptocurrency price")
        Help.add_field(name = "\u200B", value = "\u200B")
        Help.add_field(name = "\u200B", value = "\u200B")
        Help.add_field(name="$STOCK_TICKER", value="Gets the latest stock price")
        Help.add_field(name = "\u200B", value = "\u200B")
        Help.add_field(name = "\u200B", value = "\u200B")
        await message.channel.send(embed=Help)
        #function call here
    elif message.content.startswith("!"):
        await message.channel.trigger_typing()
        t = str(message.content[1:].split()[0])
        coin, cost, per = coinMarketCapPrice(t.upper())
        #If ticker not found
        if(cost == -1):
            await message.channel.send('```Ticker Not Found```')
        else:
            #Gets proper conversion (Charts under .9$ generally don't work)
            if(float(cost) < .9):
                s = '-btc'
            else:
                s = '-usdt'
            #change colors of message if coin is currently up or down
            if(float(per) < 0):
                c = discord.Colour(0xCD0000)
            elif(float(per) > 0):
                c = discord.Colour(0x00ff00)
            else:
                c = discord.Colour(0xffffff)
            #get chart
            chart = 'https://cryptohistory.org/charts/light/' + t.lower() + s +'/7d/png'
            #Creates embeded message
            embedCoin = discord.Embed(title=coin, description=t.upper() + ": $" + cost + " " + per + "% ", color = (c) )
            embedCoin.set_image(url = chart)
            await message.channel.send(embed=embedCoin)

    elif message.content.startswith("$"):
        await message.channel.trigger_typing()
        t = str(message.content[1:].split()[0])
        company, cost, per = IEXPrice(t.upper())
        #If ticker is not found
        if(cost == -1):
            await message.channel.send('```Ticker Not Found```')
        else:
            #change colors of message if stock is currently up or down
            if(float(per) < 0):
                c = discord.Colour(0xCD0000)
            elif(float(per) > 0):
                c = discord.Colour(0x00ff00)
            else:
                c = discord.Colour(0xffffff)
            #get chart (. is replace with / for things like brk.a)
            chart =  'http://c.stockcharts.com/c-sc/sc?s=' + t.upper().replace('.','/') + '&p=D&b=5&g=0&i=0'
            #Creates embeded message
            embed = discord.Embed(title=company, description=t.upper() + ": $" + str(cost) + " " + str(per) + "% ", color = (c) )
            embed.set_image(url = chart)
            await message.channel.send(embed=embed)

#coinbase price       
def coinBasePrice(x):
    TWOPLACES = Decimal(10) ** -2
    OVERPLACE =  Decimal(1000) ** -2
    current = float(requests.get('https://api.coinbase.com/v2/prices/' + x + '-USD/spot').json()['data']['amount'])
    per = round(((current/float(requests.get('https://api.pro.coinbase.com/products/' + x + '-USD/stats').json()['open']))-1)*100,2)
    current = Decimal(current).quantize(OVERPLACE) if current < .1 else Decimal(current).quantize(TWOPLACES)
    per = Decimal(per).quantize(TWOPLACES)
    return str(current), str(per)
    
#coinMarketCapPrice
#Return coin info
def coinMarketCapPrice(t):
    price = 0
    try:        
        coinInfo = requests.get('https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?&symbol=' + t, headers={'X-CMC_PRO_API_KEY' : CMK_TOKEN}).json()
        coin = coinInfo['data'][t]['name']
        try:
            cost, per = coinBasePrice(t)#gets coinbase price if avaliable 
        except:
            TWOPLACES = Decimal(10) ** -2 
            OVERPLACE =  Decimal(1000) ** -2
            cost = Decimal(coinInfo['data'][t]['quote']['USD']['price']).quantize(TWOPLACES) if  Decimal(coinInfo['data'][t]['quote']['USD']['price']) > .1 else Decimal(coinInfo['data'][t]['quote']['USD']['price']).quantize(OVERPLACE)
            per = Decimal(coinInfo['data'][t]['quote']['USD']['percent_change_24h']).quantize(TWOPLACES)
    except:
        price = -1
    #if ticker not found
    if(price == -1):
        price = -1
        return price, price, price
    return str(coin), str(cost), str(per)

#IEXPrice
#Returns stock info
def IEXPrice(t):
    try:
        stockInfo = requests.get('https://cloud.iexapis.com/stable/stock/' + (t) +'/quote?token=' + IEX_TOKEN).json()
        company = stockInfo['companyName']
        if(stockInfo['latestSource'] == 'Close'):
            if(stockInfo['extendedPrice'] == None):
                cost = stockInfo['latestPrice']
                per = stockInfo['changePercent']
            else:   
                cost = stockInfo['extendedPrice']
                per = stockInfo['extendedChangePercent']
        else:
            cost = stockInfo['latestPrice']
            per = stockInfo['changePercent']
        price = str(company) + ' $'
        price += str(round(float(cost),2)) + ' '
        price += str(round((float(per)*100),2)) + '%'
    except:
        #if ticker not found
        price = -1
        return price, price, price
    return company, round(float(cost),2), round((float(per)*100),2)

bot.run(KEY)
