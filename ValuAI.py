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

# --- 1. KONFIGURATSIYA ---
TOKEN = "8622495139:AAHGrAbMgSkDVr6_DZPDPl7V3n0jCZOHRl8"
GEMINI_API_KEY = "AIzaSyDBgMLpU4Jqc-tdMN5e4M9anUCSVa7Vsu4"

# Gemini AI ni sozlash
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

bot = Bot(token=TOKEN)
dp = Dispatcher()

class ValuationState(StatesGroup):
    choosing_lang = State()
    choosing_industry = State()
    entering_revenue = State()
    entering_growth = State()
    asking_ai = State()

# --- 2. MULTILINGUAL MATNLAR ---
MESSAGES = {
    "uz": {
        "welcome": "ValuAI ga xush kelibsiz! Startup olamiga tayyormisiz?",
        "ind": "Startupingiz qaysi sohada?",
        "rev": "Oylik daromadingizni kiriting ($):",
        "gro": "Yillik kutilayotgan o'sish sur'ati (%):",
        "res": "📊 **Taxminiy Baholash:**\n💰 Miqdor: ${low:,} - ${high:,}\n\n*Eslatma: Bu AI tahlili asosidagi taxminiy raqam.*",
        "ai_prompt": "Startupingiz haqida savol bering (masalan: Pitch deck qanday yoziladi?):"
    },
    "ru": {"welcome": "Добро пожаловать в ValuAI!", "ind": "Выберите сферу:", "rev": "Доход в месяц ($):", "gro": "Рост (%) :", "res": "📊 **Результат:** ${low:,} - ${high:,}", "ai_prompt": "Задайте вопрос о стартапе:"},
    "en": {"welcome": "Welcome to ValuAI!", "ind": "Select industry:", "rev": "Monthly revenue ($):", "gro": "Growth (%) :", "res": "📊 **Result:** ${low:,} - ${high:,}", "ai_prompt": "Ask anything about your startup:"}
}

# --- 3. KLAVIATURALAR ---
def get_main_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📊 Startupni Baholash")
    kb.button(text="🤖 AI Maslahatchi")
    kb.button(text="🚀 Venture Fondlar")
    kb.button(text="🤝 Networking")
    kb.button(text="👨‍🏫 Mentorlik")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

# --- 4. COMMAND HANDLERLAR (MENYU UCHUN) ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(MESSAGES["uz"]["welcome"], reply_markup=get_main_menu())

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Yordam bo'limi:\n1. Baholash uchun menyudan foydalaning.\n2. AI bilan gaplashish uchun 'AI Maslahatchi'ni bosing.")

@dp.message(Command("valuation"))
async def cmd_val_nav(message: types.Message, state: FSMContext):
    await start_valuation(message, state)

@dp.message(Command("mentor"))
async def cmd_mentor_nav(message: types.Message):
    await mentor(message)

# --- 5. ASOSIY FUNKSIYALAR ---

# --- STARTUPNI BAHOLASH ---
@dp.message(F.text == "📊 Startupni Baholash")
async def start_valuation(message: types.Message, state: FSMContext):
    await state.set_state(ValuationState.choosing_lang)
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇿 UZ", callback_data="lang_uz")
    builder.button(text="🇷🇺 RU", callback_data="lang_ru")
    builder.button(text="🇺🇸 EN", callback_data="lang_en")
    await message.answer("Tilni tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(ValuationState.choosing_lang)
async def lang_chosen(call: types.CallbackQuery, state: FSMContext):
    lang = call.data.split("_")[1]
    await state.update_data(lang=lang)
    await state.set_state(ValuationState.choosing_industry)
    builder = InlineKeyboardBuilder()
    for i in ["AI / ML", "Fintech", "SaaS", "E-commerce"]:
        builder.button(text=i, callback_data=f"ind_{i}")
    builder.adjust(2)
    await call.message.edit_text(MESSAGES[lang]["ind"], reply_markup=builder.as_markup())

@dp.callback_query(ValuationState.choosing_industry)
async def ind_chosen(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(industry=call.data.split("_")[1])
    data = await state.get_data()
    await state.set_state(ValuationState.entering_revenue)
    await call.message.edit_text(MESSAGES[data['lang']]["rev"])

@dp.message(ValuationState.entering_revenue)
async def rev_entered(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("Iltimos, faqat raqam kiriting!")
    await state.update_data(revenue=int(message.text))
    data = await state.get_data()
    await state.set_state(ValuationState.entering_growth)
    await message.answer(MESSAGES[data['lang']]["gro"])

@dp.message(ValuationState.entering_growth)
async def gro_entered(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("Iltimos, faqat raqam kiriting!")
    data = await state.get_data()
    rev, ind, growth = data['revenue'], data['industry'], int(message.text)
    
    mult = 15 if ind == "AI / ML" else 10 if ind == "SaaS" else 7
    val = (rev * 12) * mult * (1 + growth/100)
    
    await message.answer(MESSAGES[data['lang']]["res"].format(low=round(val*0.8), high=round(val*1.2)), reply_markup=get_main_menu())
    await state.clear()

# --- GEMINI AI MASLAHATCHI ---
@dp.message(F.text == "🤖 AI Maslahatchi")
async def ai_consultant(message: types.Message, state: FSMContext):
    await state.set_state(ValuationState.asking_ai)
    await message.answer("🚀 Men Gemini AI maslahatchisiman. Startupingiz bo'yicha qanday savolingiz bor?")

@dp.message(ValuationState.asking_ai)
async def process_ai_question(message: types.Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        return await message.answer("Asosiy menyu", reply_markup=get_main_menu())
    
    msg = await message.answer("⌛️ Gemini o'ylamoqda...")
    try:
        response = model.generate_content(f"Sen startupsing bo'yicha mutaxassis ValuAI botisan. Savolga qisqa va aniq javob ber: {message.text}")
        await msg.edit_text(response.text)
    except Exception as e:
        await msg.edit_text("Xatolik yuz berdi. Keyinroq urinib ko'ring.")
    # State ni o'chirmaymiz, foydalanuvchi yana savol berishi mumkin

# --- BOSHQA TUGMALAR ---
@dp.message(F.text == "🚀 Venture Fondlar")
async def venture(message: types.Message):
    await message.answer("🏢 **O'zbekistondagi Fondlar:**\n1. Sturgeon Capital\n2. UzVC\n3. Quest Ventures\n4. AloqaVentures")

@dp.message(F.text == "🤝 Networking")
async def networking(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Guruhga qo'shilish", url="https://t.me/startup_networ")
    await message.answer("Startupchilar va investorlar jamiyatiga qo'shiling:", reply_markup=builder.as_markup())

@dp.message(F.text == "👨‍🏫 Mentorlik")
async def mentor(message: types.Message):
    await message.answer("👨‍💻 **Asoschi va Mentor:** @ravshanov_022\nSavollaringiz bo'lsa, bemalol yozing!")

# --- 6. RENDER SERVER ---
async def handle(request): return web.Response(text="ValuAI is Running with Gemini!")

async def main():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    logging.basicConfig(level=logging.INFO)
    await asyncio.gather(site.start(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
