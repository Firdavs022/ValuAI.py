import asyncio
import logging
import os
import google.generativeai as genai
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiohttp import web

# --- 1. SOZLAMALAR ---
TOKEN = "8622495139:AAHGrAbMgSkDVr6_DZPDPl7V3n0jCZOHRl8"
GEMINI_API_KEY = "AIzaSyDBgMLpU4Jqc-tdMN5e4M9anUCSVa7Vsu4"

# Gemini AI ni sozlash
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

bot = Bot(token=TOKEN)
dp = Dispatcher()

class ValuationState(StatesGroup):
    asking_ai = State()
    choosing_lang = State()
    choosing_industry = State()
    entering_revenue = State()
    entering_growth = State()

# --- 2. KLAVIATURA ---
def get_main_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📊 Startupni Baholash")
    kb.button(text="🤖 AI Maslahatchi")
    kb.button(text="🚀 Venture Fondlar")
    kb.button(text="🤝 Networking")
    kb.button(text="👨‍🏫 Mentorlik")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

# --- 3. BUYRUQLAR (COMMANDS) ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("ValuAI botiga xush kelibsiz! Quyidagi menyudan foydalaning:", reply_markup=get_main_menu())

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Sizga qanday yordam kerak? Menyudagi tugmalarni bosing.")

# --- 4. FUNKSIYALAR ---

# VENTURE FONDLAR
@dp.message(F.text == "🚀 Venture Fondlar")
async def venture(message: types.Message):
    text = (
        "🏢 **O'zbekistondagi Venture Fondlar:**\n\n"
        "1. **AloqaVentures** - IT-startuplar uchun.\n"
        "2. **UzVC** - Milliy venchur fondi.\n"
        "3. **Sturgeon Capital** - Xalqaro investitsiya fondi.\n"
        "4. **Quest Ventures** - Markaziy Osiyo startuplari uchun."
    )
    await message.answer(text)

# NETWORKING
@dp.message(F.text == "🤝 Networking")
async def networking(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Guruhga qo'shilish", url="https://t.me/startup_networ")
    await message.answer("Startupchilar va investorlar guruhiga qo'shiling:", reply_markup=builder.as_markup())

# MENTORLIK
@dp.message(F.text == "👨‍🏫 Mentorlik")
async def mentor(message: types.Message):
    await message.answer("👨‍💻 **Asoschi va Mentor:** @ravshanov_022\nSavollaringiz bo'lsa, bemalol yozing!")

# AI MASLAHATCHI (GEMINI)
@dp.message(F.text == "🤖 AI Maslahatchi")
async def ai_consultant(message: types.Message, state: FSMContext):
    await state.set_state(ValuationState.asking_ai)
    await message.answer("🚀 Men Gemini AI maslahatchisiman. Startupingiz bo'yicha savolingizni yozing (chiqish uchun 'Orqaga' deb yozing):")

@dp.message(ValuationState.asking_ai)
async def process_ai_question(message: types.Message, state: FSMContext):
    if message.text.lower() == "orqaga":
        await state.clear()
        return await message.answer("Asosiy menyuga qaytdik.", reply_markup=get_main_menu())
    
    wait_msg = await message.answer("⌛️ Gemini o'ylamoqda...")
    try:
        response = model.generate_content(f"Sen startupsing bo'yicha mutaxassis ValuAI botisan. Savolga qisqa va aniq javob ber: {message.text}")
        await wait_msg.edit_text(response.text)
    except Exception as e:
        await wait_msg.edit_text("Hozirda AI bilan bog'lanishda muammo bo'ldi. Birozdan so'ng urinib ko'ring.")

# STARTUPNI BAHOLASH (Oddiy versiya)
@dp.message(F.text == "📊 Startupni Baholash")
async def start_valuation(message: types.Message):
    await message.answer("Ushbu funksiya hozirda optimizatsiya qilinmoqda. Tez orada ishga tushadi!")

# --- 5. RENDER SERVERNI ISHLATISH ---
async def handle(request):
    return web.Response(text="ValuAI is Live!")

async def main():
    # Render uchun port binding
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    logging.basicConfig(level=logging.INFO)
    await asyncio.gather(site.start(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
