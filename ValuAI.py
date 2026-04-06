import asyncio
import logging
import os  # <--- ENG MUHIM TUZATISH: Bu kutubxona portni aniqlash uchun shart!
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiohttp import web

# --- 1. SOZLAMALAR ---
TOKEN = "8622495139:AAHGrAbMgSkDVr6_DZPDPl7V3n0jCZOHRl8"
bot = Bot(token=TOKEN)
dp = Dispatcher()

class ValuationState(StatesGroup):
    choosing_lang = State()
    choosing_industry = State()
    entering_revenue = State()
    entering_growth = State()

# --- 2. MULTILINGUAL MATNLAR ---
MESSAGES = {
    "uz": {"welcome": "ValuAI ga xush kelibsiz!", "ind": "Sohani tanlang:", "rev": "Oylik daromad ($):", "gro": "O'sish (%) :", "res": "📊 **Natija:** ${low:,} - ${high:,}"},
    "ru": {"welcome": "Добро пожаловать!", "ind": "Выберите сферу:", "rev": "Доход в месяц ($):", "gro": "Рост (%) :", "res": "📊 **Результат:** ${low:,} - ${high:,}"},
    "en": {"welcome": "Welcome to ValuAI!", "ind": "Select industry:", "rev": "Monthly revenue ($):", "gro": "Growth (%) :", "res": "📊 **Result:** ${low:,} - ${high:,}"},
    "tr": {"welcome": "Hoş geldiniz!", "ind": "Sektör seçin:", "rev": "Aylık gelir ($):", "gro": "Büyüme (%) :", "res": "📊 **Sonuç:** ${low:,} - ${high:,}"}
}

# --- 3. KLAVIATURALAR ---
def get_main_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📊 Startupni Baholash")
    kb.button(text="🚀 Venture Fondlar")
    kb.button(text="👨‍🏫 Mentorlik")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

# --- 4. ASOSIY HANDLERLAR ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(MESSAGES["uz"]["welcome"], reply_markup=get_main_menu())

@dp.message(F.text == "📊 Startupni Baholash")
async def start_valuation(message: types.Message, state: FSMContext):
    await state.set_state(ValuationState.choosing_lang)
    builder = InlineKeyboardBuilder()
    for l in [("🇺🇿 UZ", "uz"), ("🇷🇺 RU", "ru"), ("🇺🇸 EN", "en"), ("🇹🇷 TR", "tr")]:
        builder.button(text=l[0], callback_data=f"lang_{l[1]}")
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
    if not message.text.isdigit(): return await message.answer("Faqat raqam yozing!")
    await state.update_data(revenue=int(message.text))
    data = await state.get_data()
    await state.set_state(ValuationState.entering_growth)
    await message.answer(MESSAGES[data['lang']]["gro"])

@dp.message(ValuationState.entering_growth)
async def gro_entered(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.answer("Faqat raqam yozing!")
    data = await state.get_data()
    rev, ind, growth = data['revenue'], data['industry'], int(message.text)
    
    mult = 15 if ind == "AI / ML" else 10 if ind == "SaaS" else 7
    val = (rev * 12) * mult * (1 + growth/100)
    
    await message.answer(MESSAGES[data['lang']]["res"].format(low=round(val*0.8), high=round(val*1.2)), reply_markup=get_main_menu())
    await state.clear()

@dp.message(F.text == "🚀 Venture Fondlar")
async def venture(message: types.Message):
    await message.answer("🏢 Sturgeon Capital, UzVC, Quest Ventures")

@dp.message(F.text == "👨‍🏫 Mentorlik")
async def mentor(message: types.Message):
    await message.answer("Mentor: @ravshanov_022")

# --- 5. RENDER UCHUN WEB SERVER ---
async def handle(request): return web.Response(text="ValuAI is Running!")

async def main():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    
    # Render PORT ni os orqali oladi
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    logging.basicConfig(level=logging.INFO)
    await asyncio.gather(site.start(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
