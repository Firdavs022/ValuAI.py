import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# 1. SOZLAMALAR
TOKEN = "8622495139:AAHGrAbMgSkDVr6_DZPDPl7V3n0jCZOHRl8"
bot = Bot(token=TOKEN)
dp = Dispatcher()
user_sessions = {}

# 2. XABARLAR (UZ, RU, EN, TR)
MESSAGES = {
    "uz": {
        "welcome": "🚀 ValuAI ga xush kelibsiz! Sohaga tegishli tugmani bosing:",
        "revenue": "💰 Oylik daromadingizni kiriting ($):",
        "growth": "📈 Oylik o'sish sur'ati (%):",
        "stage": "🏗 Loyiha bosqichini tanlang:",
        "result": "📊 **Tahlil Natijasi**\n━━━━━━━━━━━━━━\n📂 Soha: {ind}\n🚀 Bosqich: {stage}\n📈 O'sish: {growth}%\n━━━━━━━━━━━━━━\n💰 **Taxminiy Qiymat:**\n`${low:,}` — `${high:,}`"
    },
    "ru": {
        "welcome": "🚀 Добро пожаловать в ValuAI! Выберите сферу:",
        "revenue": "💰 Введите месячную выручку ($):",
        "growth": "📈 Ежемесячный рост (%):",
        "stage": "🏗 Выберите стадию проекта:",
        "result": "📊 **Результат анализа**\n━━━━━━━━━━━━━━\n📂 Сфера: {ind}\n🚀 Стадия: {stage}\n📈 Рост: {growth}%\n━━━━━━━━━━━━━━\n💰 **Оценка:**\n`${low:,}` — `${high:,}`"
    },
    "en": {
        "welcome": "🚀 Welcome to ValuAI! Select your industry:",
        "revenue": "💰 Enter monthly revenue ($):",
        "growth": "📈 Monthly growth rate (%):",
        "stage": "🏗 Select project stage:",
        "result": "📊 **Analysis Result**\n━━━━━━━━━━━━━━\n📂 Industry: {ind}\n🚀 Stage: {stage}\n📈 Growth: {growth}%\n━━━━━━━━━━━━━━\n💰 **Valuation:**\n`${low:,}` — `${high:,}`"
    },
    "tr": {
        "welcome": "🚀 ValuAI'ye hoş geldiniz! Sektörünüzü seçin:",
        "revenue": "💰 Aylık gelirinizi girin ($):",
        "growth": "📈 Aylık büyüme oranı (%):",
        "stage": "🏗 Proje aşamasını seçin:",
        "result": "📊 **Analiz Sonucu**\n━━━━━━━━━━━━━━\n📂 Sektör: {ind}\n🚀 Aşama: {stage}\n📈 Büyüme: {growth}%\n━━━━━━━━━━━━━━\n💰 **Değerleme:**\n`${low:,}` — `${high:,}`"
    }
}

# 3. HANDLERLAR
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇿 O'zbek tili", callback_data="lang_uz")
    builder.button(text="🇷🇺 Русский язык", callback_data="lang_ru")
    builder.button(text="🇺🇸 English", callback_data="lang_en")
    builder.button(text="🇹🇷 Türkçe", callback_data="lang_tr")
    builder.adjust(2)
    await message.answer("ValuAI: Choose language / Tilni tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("lang_"))
async def language_chosen(call: types.CallbackQuery):
    lang = call.data.split("_")[1]
    user_sessions[call.from_user.id] = {"lang": lang, "step": "industry"}
    builder = InlineKeyboardBuilder()
    for ind in ["AI / ML", "SaaS", "Fintech", "Marketplace"]:
        builder.button(text=ind, callback_data=f"ind_{ind}")
    builder.adjust(2)
    await call.message.edit_text(MESSAGES[lang]["welcome"], reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("ind_"))
async def ind_chosen(call: types.CallbackQuery):
    uid = call.from_user.id
    if uid not in user_sessions: return
    ind = call.data.split("_")[1]
    lang = user_sessions[uid]["lang"]
    user_sessions[uid].update({"industry": ind, "step": "revenue"})
    await call.message.edit_text(f"✅ {ind}\n{MESSAGES[lang]['revenue']}")

@dp.message()
async def main_logic(message: types.Message):
    uid = message.from_user.id
    if uid not in user_sessions: return
    session = user_sessions[uid]
    lang = session["lang"]
    
    if session["step"] == "revenue":
        if not message.text.replace('.', '', 1).isdigit():
            return await message.answer("⚠️ Faqat raqam kiriting!")
        session["revenue"] = float(message.text)
        session["step"] = "growth"
        await message.answer(MESSAGES[lang]["growth"])
    
    elif session["step"] == "growth":
        if not message.text.replace('.', '', 1).isdigit():
            return await message.answer("⚠️ Faqat raqam!")
        session["growth"] = float(message.text)
        session["step"] = "stage"
        builder = InlineKeyboardBuilder()
        for s in ["Idea", "MVP", "Traction", "Revenue"]:
            builder.button(text=s, callback_data=f"stage_{s}")
        await message.answer(MESSAGES[lang]["stage"], reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("stage_"))
async def final_step(call: types.CallbackQuery):
    uid = call.from_user.id
    if uid not in user_sessions: return
    stage = call.data.split("_")[1]
    data = user_sessions[uid]
    lang = data["lang"]
    
    mult = 12 if data["industry"] == "AI / ML" else 8
    val = (data["revenue"] * 12) * mult * (1 + data.get("growth", 0)/100)
    low, high = round(val * 0.8), round(val * 1.2)
    
    res = MESSAGES[lang]["result"].format(
        ind=data["industry"], stage=stage, growth=data.get("growth", 0), 
        low=low, high=high
    )
    await call.message.edit_text(res, parse_mode="Markdown")
    del user_sessions[uid]

# 4. RENDER UCHUN SOXTA SERVER (Health Check)
async def handle(request):
    return web.Response(text="Bot is running!")

# 5. ASOSIY ISHGA TUSHIRISH
async def run_bot():
    logging.basicConfig(level=logging.INFO)
    print("LOG: Bot Telegram polling rejimida ishga tushdi.")
    await dp.start_polling(bot)

async def main():
    # Render kutayotgan portni ochamiz
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = os.environ.get("PORT", "10000")
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    # Bot va Serverni bir vaqtda yurgizamiz
    await asyncio.gather(
        step1 := site.start(),
        step2 := run_bot()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
