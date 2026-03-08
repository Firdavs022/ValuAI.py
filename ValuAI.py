import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FContext
from aiohttp import web

# --- KONFIGURATSIYA ---
TOKEN = "8622495139:AAHGrAbMgSkDVr6_DZPDPl7V3n0jCZOHRl8"
bot = Bot(token=TOKEN)
dp = Dispatcher()

class ValuationState(StatesGroup):
    choosing_industry = State()
    entering_revenue = State()
    entering_growth = State()

# --- MENYU ---
def get_main_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📊 Startupni Baholash")
    kb.button(text="🚀 Venture Fondlar")
    kb.button(text="👨‍🏫 Mentorlik (Firdavs)")
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)

# --- HANDLERLAR ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f"Salom {message.from_user.full_name}! ValuAI tayyor.", reply_markup=get_main_menu())

@dp.message(F.text == "📊 Startupni Baholash")
async def start_process(message: types.Message, state: FContext):
    await state.set_state(ValuationState.choosing_industry)
    builder = InlineKeyboardBuilder()
    for i in ["AI / ML", "Fintech", "SaaS"]:
        builder.button(text=i, callback_data=f"ind_{i}")
    await message.answer("Sohani tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(ValuationState.choosing_industry, F.data.startswith("ind_"))
async def process_industry(call: types.CallbackQuery, state: FContext):
    industry = call.data.split("_")[1]
    await state.update_data(industry=industry)
    await state.set_state(ValuationState.entering_revenue)
    await call.message.edit_text(f"✅ Soha: {industry}\n\nOylik daromad ($):")

@dp.message(ValuationState.entering_revenue)
async def process_revenue(message: types.Message, state: FContext):
    if not message.text.isdigit(): return await message.answer("Raqam yozing!")
    await state.update_data(revenue=int(message.text))
    await state.set_state(ValuationState.entering_growth)
    await message.answer("Oylik o'sish (%):")

@dp.message(ValuationState.entering_growth)
async def process_growth(message: types.Message, state: FContext):
    if not message.text.isdigit(): return await message.answer("Raqam yozing!")
    data = await state.get_data()
    growth = int(message.text)
    
    # Oddiy formula
    mult = 15 if data['industry'] == "AI / ML" else 10
    valuation = (data['revenue'] * 12) * mult * (1 + (growth / 100))
    
    await message.answer(f"📊 Bahosi: ${round(valuation * 0.9):,} - ${round(valuation * 1.1):,}", reply_markup=get_main_menu())
    await state.clear()

# --- RENDER UCHUN MUHIM QISM (PORT SOZLAMASI) ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def main():
    # Render uchun veb-serverni sozlash
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render bergan PORT'ni o'qish (Hamma xato shu yerda edi)
    port = int(os.environ.get("PORT", 10000)) 
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    logging.basicConfig(level=logging.INFO)
    print(f"Server {port} portida ishga tushdi...")
    
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
