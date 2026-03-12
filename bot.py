import asyncio
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import db
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import re
import aiohttp
from aiohttp import web
import logging
from aiogram import Bot,Dispatcher,executor,types
from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton,ReplyKeyboardMarkup,KeyboardButton
from aiogram.types.web_app_info import WebAppInfo
token='8310225907:AAGvLqjogsftKvA-ZTXiKFMhrj6FX_DRGQw'
bot=Bot(token,parse_mode="HTML")
dp=Dispatcher(bot)
logging.basicConfig(level=logging.INFO)
usersettings={}
def format_game_caption(game: dict) -> str:


    return (
        f"<b>🎮 {game['name']}</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"{game['description']}\n\n"
        f"<b>💰 Price:</b> {game['price']}"
    )
def game_keyboard(app_id: int):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(
            text="🛒 Open in Steam",
            url=f"https://store.steampowered.com/app/{app_id}"
        )
    )
    keyboard.add(
        InlineKeyboardButton(
            text="⭐ Add to Wishlist",
            callback_data=f"add|{app_id}")
    )
    return keyboard
@dp.callback_query_handler(lambda c: c.data.startswith("add|"))
async def add_wishlist(call: types.CallbackQuery):
    _, game_id = call.data.split("|")
    game_id = int(game_id)
    user_id = call.from_user.id
    settings = db.get_settings(user_id)
    game = await get_game_by_id(game_id, settings["cc"], settings["l"])
    if game:
        added = db.wishlist_add(user_id, game_id, game["name"])
        if added:
            await call.answer("⭐ Added to wishlist")
        else:
            await call.answer("⚠️ Already in wishlist")
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
async def gamesearch(name):
    url='https://store.steampowered.com/api/storesearch'
    params={"term": name,
            "cc":"UA",
            "l":"English"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url,params=params) as response:
            data=await response.json()
            if data.get("total")>0:
                game=data["items"][0]
                return game["id"],game["tiny_image"]
            return None,None

async def get_game_by_id(game_id: int, cc, l):
    url = 'https://store.steampowered.com/api/appdetails'
    params = {
        "appids": game_id,
        "cc": cc,
        "l": l
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()
            if not data[str(game_id)]["success"]:
                return None
            game_data = data[str(game_id)]["data"]
            price = game_data.get("price_overview", {})
            return {
                "name": game_data.get("name"),
                "description": game_data.get("short_description"),
                "header_image": game_data.get("header_image"),
                "price": price.get("final_formatted", "Free"),
                "old_price": price.get("initial_formatted"),
                "discount": price.get("discount_percent", 0)
            }
async def test():
    game_id, image = await gamesearch("Dota 2")
    if game_id:
        game = await get_game_by_id(game_id)
        print(game)
async def api_get_games(request):
    user_id=request.rel_url.query.get("user_id")
    games=db.get_wishlist_api(user_id)
    return web.json_response(games)
def help_text():
    return (
        "<b>🤖 Game Bot – Commands</b>\n"
        "━━━━━━━━━━━━━━\n\n"

        "🔎 <b>Search game</b>\n"
        "Just type the name of any game.\n\n"

        "⭐ <b>/wishlist</b>\n"
        "Show your wishlist.\n\n"

        "📊 <b>/stats</b>\n"
        "Bot statistics.\n\n"

        "⚙ <b>/limit [percent]</b>\n"
        "Set discount notification limit.\n"
        "Example: <code>/limit 30</code>\n\n"

        "🌍 <b>/start</b>\n"
        "Select your region.\n\n"

        "💡 <b>How it works</b>\n"
        "1️⃣ Search a game\n"
        "2️⃣ Add it to wishlist\n"
        "3️⃣ Get notified when discount appears 🔥"
    )
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("Europa-EUR",callback_data="region|de|english"),
        InlineKeyboardButton("America-USD",callback_data="region|us|english"),
        InlineKeyboardButton("Ukraine-UAH",callback_data="region|ua|ukrainian")
    )

    await message.answer(
        "👋 <b>Welcome to Steam Wishlist Bot</b>\n\n"
        "First choose your region:",
        reply_markup=keyboard
    )

    await message.answer(help_text())
@dp.message_handler(commands=["help"])
async def help_command(message: types.Message):
    await message.answer(help_text())
@dp.message_handler(commands=["stats"])
async def stats(message: types.Message):
    data=db.get_allstats()
    text = (
                f"🔥 <b>Number of users-{data['users']}</b>\n"
                f"🎮 Number of games in wishlists-{data['games']}\n\n"
                f"🎮 The most popular game-{data['populargame']['name']}\n"
                f"🎮 Number of additions-{data['populargame']['count']}\n\n"
            )
    await message.answer(text)
@dp.callback_query_handler(lambda c:c.data.startswith("region|"))
async def save_region(call: types.CallbackQuery):
    r,cc,l=call.data.split("|")
    user_id=call.from_user.id
    db.user_save(user_id=user_id,name=call.from_user.full_name,cc=cc,l=l)
    await call.message.answer("Region has been set, you can write the name of the game now")
@dp.message_handler(lambda m: not m.text.startswith("/"))
async def main_game_search(message: types.Message):
    user_id = message.from_user.id
    gamename = message.text
    user_settings = db.get_settings(user_id)

    if not user_settings:
        await message.answer("❗ Please select a region first (/start)")
        return

    game_id, image = await gamesearch(gamename)

    if not game_id:
        await message.answer("❌ Game not found")
        return

    game = await get_game_by_id(
        game_id,
        user_settings["cc"],
        user_settings["l"]
    )

    if not game:
        await message.answer("⚠️ Failed to load game data")
        return

    caption = format_game_caption(game)
    clear_name = game_clear(game["name"])
    raiting = await meta_steal(clear_name)
    if raiting:
        caption += f"\n<b>⭐ Rating:</b> {raiting}"

    await message.answer_photo(
        photo=game["header_image"],
        caption=caption,
        reply_markup=game_keyboard(game_id)
    ) 
def format_wishlist(games):
    if not games:
        return "⭐ Your wishlist is empty"
    text = "<b>⭐ Your Wishlist</b>\n━━━━━━━━━━━━━━\n"
    for i, game in enumerate(games, 1):
        text += f"{i}. 🎮 {game.game_name}\n"
    return text 
def wishlist_keyboard(game_id: int):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(text="❌ Remove",callback_data=f"remove|{game_id}"))
    return kb   
@dp.message_handler(commands=["wishlist"])
async def show_wishlist(message: types.Message):
    user_id = message.from_user.id
    games = db.get_wishlist(user_id)
    if not games:
        await message.answer("⭐ Your wishlist is empty")
        return
    settings = db.get_settings(user_id)
    text = "<b>⭐ Your Wishlist</b>\n━━━━━━━━━━━━━━\n"
    for i, game in enumerate(games, 1):
        data = await get_game_by_id(game.game_id, settings["cc"], settings["l"])

        if data and data["discount"] > 0:
            text += (
                f"{i}. 🎮 {game.game_name}\n"
                f"🔥 <b>{data['discount']}% OFF</b>\n"
                f"💰 <s>{data['old_price']}</s> → <b>{data['price']}</b>\n\n"
            )
        else:
            text += f"{i}. 🎮 {game.game_name}\n💰 {data['price'] if data else 'N/A'}\n\n"
    await message.answer(text)
@dp.callback_query_handler(lambda c: c.data.startswith("remove|"))
async def remove_from_wishlist(call: types.CallbackQuery):
    _, game_id = call.data.split("|")
    if not game_id or game_id == "None":
        await call.answer("⚠️ Invalid game ID", show_alert=True)
        return
    game_id = int(game_id)
    user_id = call.from_user.id
    success = db.wishlist_delete(user_id, game_id)
    if success:
        await call.answer("❌ Removed from wishlist", show_alert=True)
        await call.message.delete()
    else:
        await call.answer("⚠️ Not found", show_alert=True)
async def check_discount():
    users = db.get_users()

    for user in users:
        games = db.get_wishlist(user.id)

        if not games:
            continue

        settings = db.get_settings(user.id)
        discount_limit = settings["dl"] or 0

        text = "<b>🔥 Discounts on your wishlist</b>\n━━━━━━━━━━━━━━\n"
        has_discount = False

        for i, game in enumerate(games, 1):
            data = await get_game_by_id(
                game.game_id,
                settings["cc"],
                settings["l"]
            )

            if data and data["discount"] >= discount_limit:
                has_discount = True
                text += (
                    f"{i}. 🎮 {game.game_name}\n"
                    f"🔥 <b>{data['discount']}% OFF</b>\n"
                    f"💰 <s>{data['old_price']}</s> → <b>{data['price']}</b>\n\n"
                )
        if has_discount:
            await bot.send_message(user.id, text)
@dp.message_handler(commands=["limit"])
async def limit(message: types.Message):
    user_id = message.from_user.id
    args = message.get_args()

    if not args:
        await message.answer("Usage: /limit 30  (number = percent)")
        return

    if not args.isdigit():
        await message.answer("❗ Please enter a valid number")
        return

    discount_value = int(args)

    if discount_value < 0 or discount_value > 100:
        await message.answer("❗ Discount must be between 0 and 100")
        return

    success = db.set_discount(user_id, discount_value)

    if success:
        await message.answer(f"✅ Discount limit set to {discount_value}%")
    else:
        await message.answer("⚠️ You need to select region first (/start)")
@dp.message_handler(commands=["app"])
async def app_open(message: types.Message):
    url="https://game-bot-112i.onrender.com"
    keybord=ReplyKeyboardMarkup()
    button=KeyboardButton(text="🔥New format app!🔥",web_app=WebAppInfo(url=url))
    keybord.add(button)
    await message.answer("🔥Press button for new goated format🔥",reply_markup=keybord)
async def rofl(request):
    with open("bot.html","r",encoding="UTF-8") as page:
        content=page.read()
    return web.Response(text=content,content_type="text/html")
async def on_startup(dp):
    scheduler=AsyncIOScheduler()
    scheduler.add_job(check_discount,"interval",days=1)
    scheduler.start()
    app=web.Application()
    app.router.add_get("/",rofl)
    app.router.add_get("/api/games",api_get_games)
    run=web.AppRunner(app)
    await run.setup()
    port=int(os.environ.get("PORT",10000))
    site=web.TCPSite(run,"0.0.0.0",port)
    await site.start()
    print("started") 

    #думать              


























if __name__=="__main__":
    executor.start_polling(dp,on_startup=on_startup)
