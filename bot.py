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
CHATTERFY_TOKEN = os.environ["CHATTERFY_TOKEN"]
CHATTERFY_BOT_ID = os.environ["CHATTERFY_BOT_ID"]

claude = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привіт! Я AI-асистент для саппорту.\n\n"
        "Надішли мені Chat ID діалогу з Chatterfy і я проаналізую переписку та підкажу як відповісти клієнту."
    )

async def analyze_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id_input = update.message.text.strip()

    await update.message.reply_text("⏳ Завантажую переписку з Chatterfy...")

    url = f"https://api.chatterfy.ai/api/bots/{CHATTERFY_BOT_ID}/chats/{chat_id_input}/messages?limit=0&offset=0"
    headers = {
        "Authorization": CHATTERFY_TOKEN,
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Origin": "https://app.chatterfy.ai",
        "Referer": "https://app.chatterfy.ai/"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            await update.message.reply_text(
                f"❌ Не вдалось отримати переписку.\n"
                f"Статус: {response.status_code}\n"
                f"Перевір Chat ID."
            )
            return

        data = response.json()

        # Логуємо що прийшло для діагностики
        logging.info(f"Chatterfy response: {str(data)[:500]}")

        # Витягуємо список повідомлень з різних форматів
        if isinstance(data, list):
            messages = data
        elif isinstance(data, dict):
            messages = data.get("data") or data.get("messages") or data.get("items") or []
        else:
            messages = []

        if not messages:
            await update.message.reply_text(f"❌ Переписка порожня.\nВідповідь API: {str(data)[:200]}")
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
            model="claude-sonnet-4-5",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": f"""Ти досвідчений sales-менеджер і коуч. Проаналізуй переписку між менеджером і клієнтом та дай конкретні рекомендації.

ПЕРЕПИСКА:
{conversation_text}

Надай:
1. АНАЛІЗ СИТУАЦІЇ — що відбувається, які заперечення або проблеми у клієнта
2. СТРАТЕГІЯ — як правильно вести далі цей діалог
3. ГОТОВІ ФРАЗИ — 2-3 конкретних варіанти що написати клієнту прямо зараз

Відповідай українською мовою, конкретно і по суті."""
                }
            ]
        )

        advice = claude_response.content[0].text
        await update.message.reply_text(f"Аналіз діалогу:\n\n{advice}")

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
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            await update.message.reply_text(
                f"❌ Не вдалось отримати переписку.\n"
                f"Статус: {response.status_code}\n"
                f"Перевір Chat ID."
            )
            return

        data = response.json()

        # Логуємо що прийшло для діагностики
        logging.info(f"Chatterfy response: {str(data)[:500]}")

        # Витягуємо список повідомлень з різних форматів
        if isinstance(data, list):
            messages = data
        elif isinstance(data, dict):
            messages = data.get("data") or data.get("messages") or data.get("items") or []
        else:
            messages = []

        if not messages:
            await update.message.reply_text(f"❌ Переписка порожня.\nВідповідь API: {str(data)[:200]}")
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
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": f"""Ти досвідчений sales-менеджер і коуч. Проаналізуй переписку між менеджером і клієнтом та дай конкретні рекомендації.

ПЕРЕПИСКА:
{conversation_text}

Надай:
1. АНАЛІЗ СИТУАЦІЇ — що відбувається, які заперечення або проблеми у клієнта
2. СТРАТЕГІЯ — як правильно вести далі цей діалог
3. ГОТОВІ ФРАЗИ — 2-3 конкретних варіанти що написати клієнту прямо зараз

Відповідай українською мовою, конкретно і по суті."""
                }
            ]
        )

        advice = claude_response.content[0].text
        await update.message.reply_text(f"Аналіз діалогу:\n\n{advice}")

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
