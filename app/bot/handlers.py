import asyncio
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from app.database import SessionLocal
from app.models import User, Game, wishlist_association
from app.services.steam import steam_service
from app.bot.keyboards import get_main_keyboard

bot_router = Router()

def db_start_user(user_id, username, first_name):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            user = User(telegram_id=user_id, username=username, first_name=first_name)
            db.add(user)
            db.commit()

def db_get_user_games(user_id):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if user:
            return [{"title": g.title, "current_price": g.current_price, "discount_percent": g.discount_percent, "steam_app_id": g.steam_app_id} for g in user.tracked_games]
        return []

def db_delete_game(user_id, game_id):
    with SessionLocal() as db:
        stmt = wishlist_association.delete().where(
            (wishlist_association.c.user_id == user_id) & 
            (wishlist_association.c.game_id == game_id)
        )
        db.execute(stmt)
        db.commit()

def db_add_game(user_id, app_id, steam_data):
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            return "user_not_found"
            
        is_tracked = db.query(wishlist_association).filter_by(user_id=user_id, game_id=app_id).first()
        if is_tracked:
            return "already_exists"
            
        game = db.query(Game).filter(Game.steam_app_id == app_id).first()
        if not game and steam_data:
            game = Game(
                steam_app_id=app_id,
                title=steam_data["title"],
                current_price=steam_data["current_price"],
                initial_price=steam_data["initial_price"],
                discount_percent=steam_data["discount_percent"]
            )
            db.add(game)
            db.flush()
            
        if game:
            user.tracked_games.append(game)
            db.commit()
            return game.title, game.current_price
        return "error"

@bot_router.message(CommandStart())
async def cmd_start(message: Message):
    await asyncio.to_thread(db_start_user, message.from_user.id, message.from_user.username, message.from_user.first_name)
    await message.answer(
        f"Привет, {message.from_user.first_name}! Я помогу тебе следить за скидками в Steam.\n\n"
        "Чтобы добавить игру в список отслеживания, просто отправь мне её ссылку или ID.\n"
        "Например: `2357570` или ссылку на магазин.",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

# Обрабатывает команду и с эмодзи, и без
@bot_router.message(F.text.in_(["📋 Мой список", "Мой список"]))
async def show_wishlist(message: Message):
    games = await asyncio.to_thread(db_get_user_games, message.from_user.id)
    
    if not games:
        await message.answer("Твой список отслеживания пока пуст.")
        return
        
    response = "Твои отслеживаемые игры:\n\n"
    for game in games:
        response += (
            f"**{game['title']}**\n"
            f"Цена: {game['current_price']} руб. (Скидка: {game['discount_percent']}%)\n"
            f"ID: `{game['steam_app_id']}`\n\n"
        )
    await message.answer(response, parse_mode="Markdown")

# Обрабатывает команду и с эмодзи, и без
@bot_router.message(F.text.in_(["❓ Помощь", "Помощь"]))
async def cmd_help(message: Message):
    await message.answer(
        "Как пользоваться ботом:\n\n"
        "1. Отправь ID игры (цифры из ссылки Steam) или полную ссылку на игру, чтобы начать отслеживание.\n"
        "2. Нажми 'Мой список', чтобы увидеть текущие цены.\n"
        "3. Нажми 'Удалить игру', а затем отправь ID, чтобы убрать её."
    )

# Обрабатывает команду и с эмодзи, и без
@bot_router.message(F.text.in_(["🗑 Удалить игру", "Удалить игру"]))
async def delete_prompt(message: Message):
    await message.answer("Чтобы удалить игру, отправь команду `/del ID` (например: `/del 2357570`).", parse_mode="Markdown")

@bot_router.message(Command("del"))
async def cmd_delete(message: Message):
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("Укажи корректный ID игры. Пример: `/del 2357570`")
        return
        
    game_id = int(args[1])
    await asyncio.to_thread(db_delete_game, message.from_user.id, game_id)
    await message.answer(f"Игра с ID {game_id} успешно удалена из твоего списка.")

@bot_router.message()
async def process_game_input(message: Message):
    text = message.text.strip()
    
    # Полный список системных фраз (с эмодзи и без), которые бот должен игнорировать в этом хэндлере
    if text in ["📋 Мой список", "Мой список", "❓ Помощь", "Помощь", "🗑 Удалить игру", "Удалить игру"]:
        return

    if "store.steampowered.com/app/" in text:
        try:
            parts = text.split("app/")[1].split("/")
            app_id_str = parts[0]
        except Exception:
            await message.answer("Не удалось распознать ссылку. Отправь просто ID игры чистыми цифрами.")
            return
    else:
        app_id_str = text

    if not app_id_str.isdigit():
        await message.answer("Отправь корректный числовой ID игры или ссылку из Steam.")
        return
        
    app_id = int(app_id_str)
    
    def check_exists():
        with SessionLocal() as db:
            return bool(db.query(wishlist_association).filter_by(user_id=message.from_user.id, game_id=app_id).first())
            
    exists = await asyncio.to_thread(check_exists)
    if exists:
        await message.answer("Эта игра уже есть в твоем списке отслеживания!")
        return

    await message.answer("Ищу игру в Steam, подожди секунду...")
    steam_data = await steam_service.get_game_details(app_id)
    
    if not steam_data:
        await message.answer("Не удалось найти такую игру в Steam. Проверь ID.")
        return
        
    res = await asyncio.to_thread(db_add_game, message.from_user.id, app_id, steam_data)
    
    if res == "already_exists":
        await message.answer("Эта игра уже есть в твоем списке отслеживания!")
    elif res == "user_not_found":
        await message.answer("Ошибка: сначала введи команду /start")
    elif res == "error":
        await message.answer("Произошла ошибка при добавлении игры.")
    else:
        title, price = res
        await message.answer(f"Игра **{title}** добавлена!\nТекущая цена: {price} руб.", parse_mode="Markdown")