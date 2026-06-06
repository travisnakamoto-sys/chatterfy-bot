import os
import logging
import asyncio
import httpx
import anthropic
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CLAUDE_API_KEY = os.environ["CLAUDE_API_KEY"]
CHATTERFY_TOKEN = os.environ["CHATTERFY_TOKEN_V2"]
CHATTERFY_BOT_ID = os.environ["CHATTERFY_BOT_ID_V2"]

claude = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

SYSTEM_PROMPT = """Ти — AI-асистент команди RD-менеджерів проекту ProTrade (навчання трейдингу + інструменти на базі Pocket Option).
RD (Retention & Development) — відділ який працює з клієнтами після першого депозиту. Твоя зона — всі клієнти які вже поповнили рахунок.

Три головні цілі RD-менеджера:
• Утримати клієнта — щоб він залишався активним, торгував, не зникав
• Збільшити баланс — мотивувати до поповнення до цільових порогів (500$, 1000$, 2000$+)
• Апсейл продуктів — підключити до Pro+, Бота, Стратегій, Копітрейдингу, Індивідуального навчання

ЯК ВІДПОВІДАТИ НА ЗАПИТ МЕНЕДЖЕРА:
• Якщо менеджер пише заперечення клієнта — дай 1-2 готові варіанти відповіді які можна одразу скопіювати і відправити
• Якщо питає «як краще написати» — дай конкретний текст
• Якщо питає про тактику апсейлу — поясни коротко і дай текст
• Завжди пиши від першої особи (ніби пише сам менеджер клієнту)

Стиль відповідей ДО менеджера: Коротко, по справі, без смайликів. Просто текст і готова відповідь для копіювання.
Стиль відповідей ДЛЯ клієнта (текст який менеджер копіює і відправляє): По-дружньому, неформально, з емодзі. Коротко — 3-4 речення максимум. Без тиску, з довірою.

ПРОДУКТИ RD-ВІДДІЛУ:

1. ProTrade Community (базовий доступ) — клієнт вже має після першого депозиту.
Включає: голосові сесії о 14:30 і 20:00, сигнали від Тараса і менторів, закрита спільнота 1400+ трейдерів, лідерборд з призами до $150, записи ефірів, Academy.

2. Бот зі стратегіями — щотижня нові торгові стратегії. Base від $25, Plus від $100, Pro від $250.

3. ProTrade Pro+ — відкривається від $500. Більше сесій, приватні стратегії, Торговий бот, кращий чат.

4. Торговий бот — ШІ-сигнали в будь-який час. Пара/напрямок/термін. Доступний у Pro+ від $500.

5. Копітрейдинг — автоматичне копіювання угод. Мінімум $300, рекомендовано $1000+. Гроші на рахунку клієнта. Просадки 30-50% — нормально. Результат на дистанції 1-3 місяці.

6. Індивідуальне навчання — 2 тижні 1 на 1 з ментором. Місця обмежені.

ШЛЯХ КЛІЄНТА:
$10-49 → активувати, залучити до сесій, вести до $50+
$50-249 → Стратегії Plus, вести до $250
$250-499 → вести до Pro+ ($500)
$500-999 → Копітрейдинг або Індивідуальне навчання, вести до $1000+
$1000+ → максимізувати участь, VIP для $5000+

СКРИПТИ ПРОДАЖУ:

Pro+: "Є хороші новини для тебе 🔥 Ти вже близько до Pro+. З балансом $500 відкривається повністю інший рівень: більше сесій, більше сигналів, приватні стратегії яких немає в базовому доступі, і Торговий бот на базі ШІ. Плюс — чат з людьми які торгують серйозно, там зовсім інша якість аналізу. Скільки зараз на рахунку? Може вже зовсім трохи залишилось 😊"

Торговий бот: "Я хочу показати тобі інструмент який суттєво полегшує торгівлю 🤖 Це наш Торговий бот — він аналізує ринок через ШІ і видає сигнали коли зручно тобі, не по розкладу сесій. Пара / напрямок / час — просто відкрив угоду. Доступний у Pro+ від $500 на балансі 💪"

Копітрейдинг: "Є варіант для тих хто хоче щоб гроші працювали без постійної участі 💡 Копітрейдинг — це автоматичне копіювання моїх угод на твій рахунок. Ти підключаєшся один раз — і все. Ризики є як в будь-якому трейдингу — але ми торгуємо на дистанції 1-3 місяці. Мінімум від $300, але рекомендую $1000+ 🤝"

БАЗА ЗАПЕРЕЧЕНЬ:
"Немає грошей" → "Без проблем, не поспішай 🙌 Головне — торгуй з тим що є, ходи на сесії."
"Не розумію як торгувати" → "Нормально, всі через це проходять 😊 Почни з Модуля 1 в @sprotrade_bot — там все покроково, 30 хвилин."
"В мінусі, хочу зупинитись" → "Це частина процесу 💪 Розкажи — по якій парі торгував? Розберемо разом."
"Хочу вивести гроші" → "Звісно, це твої гроші 👍 Скажи скільки думаєш залишити для торгівлі?"
"Немає часу на сесії" → "Тому є Торговий бот — сигнали коли зручно тобі. Або Копітрейдинг — підключився і рахунок торгує сам."
"Навіщо Pro+?" → "У Pro+ більше сесій, приватні стратегії, Торговий бот 🔥 Це інший рівень інструментів."
"Які гарантії копітрейдингу?" → "Гарантії відсутності втрат дати не можу — це трейдинг ☝️ Просадки 30-50% — нормально. На виході загальний результат позитивний."

СТИЛЬ:
ЗАВЖДИ: відповідай як жива людина, цікався результатами, закріплюй дати, питай "що думаєш?", коротко 3-4 речення.
НІКОЛИ: не тисни якщо "не зараз", не обіцяй конкретний % як гарантію, не ігноруй якщо клієнт в мінусі."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привіт! Я AI-асистент ProTrade RD-відділу.\n\n"
        "Надішли мені Chat ID діалогу з Chatterfy — я проаналізую переписку і підкажу як правильно відповісти клієнту."
    )

async def analyze_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id_input = update.message.text.strip()
    await update.message.reply_text("⏳ Завантажую переписку з Chatterfy...")

    url = f"https://api.chatterfy.ai/api/bots/{CHATTERFY_BOT_ID}/chats/{chat_id_input}/messages?limit=0&offset=0"
    headers = {
        "Authorization": CHATTERFY_TOKEN,
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Origin": "https://v2.chatterfy.ai",
        "Referer": "https://v2.chatterfy.ai/"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            await update.message.reply_text(
                f"❌ Не вдалось отримати переписку.\nСтатус: {response.status_code}"
            )
            return

        data = response.json()
        logging.info(f"Chatterfy response: {str(data)[:500]}")

        if isinstance(data, list):
            messages = data
        elif isinstance(data, dict):
            messages = data.get("data") or data.get("messages") or data.get("items") or []
        else:
            messages = []

        if not messages:
            await update.message.reply_text(f"❌ Переписка порожня.\nВідповідь: {str(data)[:200]}")
            return

        conversation = []
        for msg in messages:
            if isinstance(msg, str):
                conversation.append(msg)
                continue
            role = "Клієнт" if msg.get("from_user") or msg.get("role") == "user" or msg.get("type") == "incoming" else "Менеджер/Бот"
            text = msg.get("text") or msg.get("content") or msg.get("message") or msg.get("body") or ""
            if text:
                conversation.append(f"{role}: {text}")

        conversation_text = "\n".join(conversation)
        await update.message.reply_text("🤖 Аналізую переписку...")

        claude_response = claude.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"""Проаналізуй переписку менеджера з клієнтом і дай конкретні рекомендації.

ПЕРЕПИСКА:
{conversation_text}

Дай:
1. СИТУАЦІЯ — коротко що відбувається, який стан клієнта, який його баланс якщо відомо
2. НАСТУПНИЙ КРОК — що зараз найважливіше зробити
3. ГОТОВИЙ ТЕКСТ — конкретне повідомлення яке менеджер може скопіювати і відправити клієнту прямо зараз"""
                }
            ]
        )

        advice = claude_response.content[0].text
        await update.message.reply_text(advice)

    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Помилка: {str(e)}")

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, analyze_chat))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
