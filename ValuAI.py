import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FContext
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

# --- 2. MULTILINGUAL MATNLAR (4 TA TIL) ---
MESSAGES = {
    "uz": {
        "welcome": "Assalomu Alaykum! ValuAI ga xush kelibsiz. Quyidagilardan birini tanlang:",
        "ind": "1️⃣ **Sohani tanlang:**",
        "rev": "2️⃣ **Oylik sof daromad ($):**",
        "gro": "3️⃣ **Oylik o'sish sur'ati (%):**",
        "res": "📊 **TAHLIL NATIJASI**\n" + "━"*15 + "\n💰 **Qiymat:** ${low:,} — ${high:,}\n" + "━"*15
    },
    "ru": {
        "welcome": "Добро пожаловать в ValuAI! Выберите действие:",
        "ind": "1️⃣ **Выберите сферу:**",
        "rev": "2️⃣ **Ежемесячная выручка ($):**",
        "gro": "3️⃣ **Темп роста (%):**",
        "res": "📊 **РЕЗУЛЬТАТ ОЦЕНКИ**\n" + "━"*15 + "\n💰 **Стоимость:** ${low:,} — ${high:,}\n" + "━"*15
    },
    "en": {
        "welcome": "Welcome to ValuAI! Please select an option:",
        "ind": "1️⃣ **Select industry:**",
        "rev": "2️⃣ **Monthly revenue ($):**",
        "gro": "3️⃣ **Monthly growth rate (%):**",
        "res": "📊 **VALUATION RESULT**\n" + "━"*15 + "\n💰 **Value:** ${low:,} — ${high:,}\n" + "━"*15
    },
    "tr": {
        "welcome": "ValuAI'ye hoş geldiniz! Bir seçenek belirleyin:",
        "ind": "1️⃣ **Sektör seçin:**",
        "rev": "2️⃣ **Aylık gelir ($):**",
        "gro": "3️⃣ **Aylık büyüme oranı (%):**",
        "res": "📊 **DEĞERLEME SONUCU**\n" + "━"*15 + "\n💰 **Değer:** ${low:,} — ${high:,}\n" + "━"*15
    }
}

# --- 3. MENYU VA TUGMALAR ---
def get_main_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📊 Startupni Baholash")
    kb.button(text="🚀 Venture Fondlar")
    kb.button(text="👨‍🏫 Mentorlik (Firdavs)")
    kb.button(text="📂 Loyihalar (Maestro)")
    kb.adjust(2, 2)
    return kb.as_markup(resize_keyboard=True)

# --- 4. ASOSIY MANTIQ (HANDLERLAR) ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(MESSAGES["uz"]["welcome"], reply_markup=get_main_menu())

@dp.message(F.text == "📊 Startupni Baholash")
async def start_valuation(message: types.Message, state: FContext):
    await state.set_state(ValuationState.choosing_lang)
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇿 UZ", callback_data="lang_uz")
    builder.button(text="🇷🇺 RU", callback_data="lang_ru")
    builder.button(text="🇺🇸 EN", callback_data="lang_en")
    builder.button(text="🇹🇷 TR", callback_data="lang_tr")
    await message.answer("Tilni tanlang / Выберите язык / Select language:", reply_markup=builder.as_markup())

@dp.callback_query(ValuationState.choosing_lang)
async def lang_chosen(call: types.CallbackQuery, state: FContext):
    lang = call.data.split("_")[1]
    await state.update_data(lang=lang)
    await state.set_state(ValuationState.choosing_industry)
    
    builder = InlineKeyboardBuilder()
    for i in ["AI / ML", "Fintech", "SaaS", "E-commerce"]:
        builder.button(text=i, callback_data=f"ind_{i}")
    builder.adjust(2)
    await call.message.edit_text(MESSAGES[lang]["ind"], reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(ValuationState.choosing_industry)
async def ind_chosen(call: types.CallbackQuery, state: FContext):
    industry = call.data.split("_")[1]
    data = await state.get_data()
    lang = data['lang']
    await state.update_data(industry=industry)
    await state.set_state(ValuationState.entering_revenue)
    await call.message.edit_text(f"✅ {industry}\n\n{MESSAGES[lang]['rev']}", parse_mode="Markdown")

@dp.message(ValuationState.entering_revenue)
async def rev_entered(message: types.Message, state: FContext):
    if not message.text.isdigit(): return await message.answer("⚠️ Faqat raqam!")
    data = await state.get_data()
    lang = data['lang']
    await state.update_data(revenue=int(message.text))
    await state.set_state(ValuationState.entering_growth)
    await message.answer(MESSAGES[lang]["gro"], parse_mode="Markdown")

@dp.message(ValuationState.entering_growth)
async def gro_entered(message: types.Message, state: FContext):
    if not message.text.isdigit(): return await message.answer("⚠️ Faqat raqam!")
    data = await state.get_data()
    lang, rev, ind = data['lang'], data['revenue'], data['industry']
    growth = int(message.text)
    
    mult = 18 if ind == "AI / ML" else 12 if ind == "SaaS" else 8
    val = (rev * 12) * mult * (1 + growth/100)
    
    await message.answer(
        MESSAGES[lang]["res"].format(low=round(val*0.85), high=round(val*1.15)),
        reply_markup=get_main_menu(), parse_mode="Markdown"
    )
    await state.clear()

@dp.message(F.text == "🚀 Venture Fondlar")
async def venture(message: types.Message):
    text = "🏢 **Venture Fondlar:**\n1. Sturgeon Capital\n2. UzVC\n3. Quest Ventures"
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "👨‍🏫 Mentorlik (Firdavs)")
async def mentor(message: types.Message):
    await message.answer("Firdavs Ravshanov: @ravshanov_022")

# --- 5. RENDER UCHUN WEB SERVER (24/7 UCHUN) ---
async def handle(request): return web.Response(text="Bot is Live!")

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
