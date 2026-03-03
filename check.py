import asyncio
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
import aiohttp
import logging
from aiogram import Bot,Dispatcher,executor,types
from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton
import requests
def game_clear(name:str):
    name=name.lower()
    name=name.replace("&","and")
    name=re.sub(r"[^a-z0-9\s-]","",name)
    name=re.sub(r"\s+","-",name)
    return name.strip("-")
async def meta_steal(name):
    name=game_clear(name)
    url=f"https://www.metacritic.com/game/{name}/"
    agent=UserAgent()
    headers={
        'User-Agent': agent.random,
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url,headers=headers) as response:
            html=await response.text()
            soup=BeautifulSoup(html,"html.parser")
            score=soup.find("div",class_="c-productScoreInfo_scoreNumber")
            if score:
                result=score.find("span").text.strip()
                return result

    


if __name__=="__main__":
   result=asyncio.run(meta_steal("Dota 2"))
print(result)