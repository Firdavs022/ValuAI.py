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

# --- MATNLAR ---
MESSAGES = {
    "uz": {
        "ind": "1️⃣ **Startupingiz qaysi yo'nalishda?**",
        "rev": "2️⃣ **Oylik sof daromadingiz (Revenue) qancha?** ($ larda yozing)",
        "gro": "3️⃣ **Oylik o'rtacha o'sish sur'ati (Growth) necha foiz?** (%)",
        "res": "📊 **VALUAI PROFESSIONAL TAHLILI**\n" + "━" * 15 + "\n"
               "📂 **Soha:** {ind}\n📈 **O'sish:** {gro}%\n💰 **Oylik daromad:** ${rev:,}\n" + "━" * 15 + "\n"
               "🚀 **TAXMINIY BOZOR QIYMATI:**\n"
               "💎 **${low:,} — ${high:,}**\n\n"
               "💡 *Ushbu qiymat joriy bozor multiplikatorlari asosida hisoblandi.*"
    }
}

# --- MENYU ---
def get_main_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="📊 Startupni Baholash")
    kb.button(text="🚀 Venture Fondlar")
    kb.button(text="👨‍🏫 Mentorlik (Firdavs)")
    kb.button(text="📂 Loyihalar (Maestro)")
    kb.adjust(2, 1)
    return kb.as_markup(resize_keyboard=True)

# --- HANDLERLAR ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"Assalomu Alaykum, **{message.from_user.full_name}**! 👋\n\n"
        "**ValuAI** — Startup qiymatini aniqlash professional platformasi.",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@dp.message(F.text == "📊 Startupni Baholash")
async def start_process(message: types.Message, state: FContext):
    await state.set_state(ValuationState.choosing_industry)
    builder = InlineKeyboardBuilder()
    for i in ["AI / ML", "Fintech", "SaaS", "E-commerce"]:
        builder.button(text=i, callback_data=f"ind_{i}")
    builder.adjust(2)
    await message.answer(MESSAGES["uz"]["ind"], reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(ValuationState.choosing_industry, F.data.startswith("ind_"))
async def process_industry(call: types.CallbackQuery, state: FContext):
    industry = call.data.split("_")[1]
    await state.update_data(industry=industry)
    await state.set_state(ValuationState.entering_revenue)
    await call.message.edit_text(f"✅ **Soha:** {industry}\n\n{MESSAGES['uz']['rev']}", parse_mode="Markdown")

@dp.message(ValuationState.entering_revenue)
async def process_revenue(message: types.Message, state: FContext):
    text = message.text.replace('$', '').replace(',', '').strip()
    if not text.isdigit():
        return await message.answer("⚠️ Iltimos, faqat raqam kiriting!")
    await state.update_data(revenue=int(text))
    await state.set_state(ValuationState.entering_growth)
    await message.answer(MESSAGES["uz"]["gro"], parse_mode="Markdown")

@dp.message(ValuationState.entering_growth)
async def process_growth(message: types.Message, state: FContext):
    text = message.text.replace('%', '').strip()
    if not text.isdigit():
        return await message.answer("⚠️ Iltimos, faqat raqam kiriting!")
    
    data = await state.get_data()
    growth = int(text)
    rev = data['revenue']
    ind = data['industry']

    mult = 18 if ind == "AI / ML" else 12 if ind == "SaaS" else 8
    valuation = (rev * 12) * mult * (1 + (growth / 100))
    low, high = round(valuation * 0.85), round(valuation * 1.15)
    
    await message.answer(
        MESSAGES["uz"]["res"].format(ind=ind, gro=growth, rev=rev, low=low, high=high),
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )
    await state.clear()

@dp.message(F.text == "👨‍🏫 Mentorlik (Firdavs)")
async def mentor(message: types.Message):
    btn = InlineKeyboardBuilder()
    btn.button(text="📩 Bog'lanish", url="https://t.me/ravshanov_022")
    await message.answer("Mentorlik uchun murojaat qiling:", reply_markup=btn.as_markup())

@dp.message(F.text == "🚀 Venture Fondlar")
async def venture(message: types.Message):
    text = "🏢 **Venture Fondlar:**\n1. Sturgeon Capital\n2. UzVC\n3. Quest Ventures"
    await message.answer(text, parse_mode="Markdown")

# --- RENDER WEB SERVER ---
async def handle(request):
    return web.Response(text="ValuAI Status: Active")

async def main():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    logging.basicConfig(level=logging.INFO)
    print(f"Bot {port}-portda ishlamoqda...")
    
    # Bir vaqtda ham serverni, ham botni yurgizish
    await asyncio.gather(site.start(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
