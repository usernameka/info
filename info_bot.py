# -*- coding: utf-8 -*-
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                                               #
#        ለ Vercel የተስተካከለ ሁለገብ መረጃ አግኚ ቦት (Info Bot)      #
#                 V.2 - Initialization ስህተት የተስተካከለበት          #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
import logging
import os
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# ሎጊንግን ማዋቀር
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ከ Environment Variable ቶክኑን መውሰድ
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN የሚባል Environment Variable አልተገኘም!")

# Flask አፕሊኬሽኑን መፍጠር
app = Flask(__name__)

# --------------------------- ዋና ዋና ፊቸሮች ---------------------------

def estimate_account_age(user_id: int) -> str:
    """የአካውንት ዕድሜ ይገምታል"""
    known_ids = {
        100000000: "2015", 500000000: "2017", 1000000000: "2019",
        2000000000: "2021", 5000000000: "2022", 6000000000: "2023",
        7000000000: "2024",
    }
    year_created = "ከ 2015 በፊት"
    for id_milestone, year in known_ids.items():
        if user_id > id_milestone:
            year_created = year
        else:
            break
    return f"📅 በግምት በ {year_created} ወይም ከዚያ በኋላ የተከፈተ።"

async def analyze_scam_potential(user: 'User', bot_instance: Bot, user_id: int) -> str:
    """የማጭበርበር ስጋትን ይመረምራል"""
    warnings = []
    try:
        profile_photos = await bot_instance.get_user_profile_photos(user_id, limit=1)
        if profile_photos.total_count == 0:
            warnings.append("• 🖼️ ፕሮፋይል ፎቶ የለውም።")
    except Exception as e:
        logger.warning(f"Could not fetch profile photos for {user_id}: {e}")

    if not user.username:
        warnings.append("• ✍️ Username አልተቀመጠለትም።")

    suspicious_keywords = ['admin', 'support', 'telegram', 'premium', 'service']
    full_name = (user.first_name + " " + (user.last_name or "")).lower()
    for keyword in suspicious_keywords:
        if keyword in full_name:
            warnings.append(f"• 📛 ስሙ '{keyword.capitalize()}' የሚል አጠራጣሪ ቃል ይዟል።")

    if not warnings:
        return "✅ ምንም አጠራጣሪ ነገር አልተገኘም።"
    else:
        return "⚠️ **የደህንነት ትንታኔ:**\n" + "\n".join(warnings)

# --------------------------- የቦት ትዕዛዝ እና ምላሾች ---------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome_message = (
        f"👋 ሰላም {user.mention_html()}!\n\n"
        "እኔ ሁለገብ መረጃ አግኚ ቦት ነኝ። ስለማንኛውም የቴሌግራም ተጠቃሚ፣ ቻናል ወይም ግሩፕ መረጃ ማግኘት ከፈለጉ፣\n\n"
        "1. ከአንድ ሰው ወይም ቻናል የተላከን መልዕክት ወደ እኔ `Forward` ያድርጉ።\n"
        "2. `/id` የሚለውን ትዕዛዝ በመላክ የራስዎን ወይም የግሩፑን ID ያግኙ።"
    )
    await update.message.reply_html(welcome_message)

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = f"👤 **የእርስዎ User ID:** `{user.id}`\n"
    if chat.id != user.id:
        message += f"💬 **የዚህ ግሩፕ/ቻናል ID:** `{chat.id}`"
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)

async def forward_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message.forward_from_chat:
        chat = message.forward_from_chat
        response = (
            f"📢 **የቻናል/ግሩፕ መረጃ**\n\n"
            f"**ስም:** {chat.title}\n"
            f"**Username:** @{chat.username if chat.username else 'የለውም'}\n"
            f"**Chat ID:** `{chat.id}`"
        )
        await message.reply_text(response, parse_mode=ParseMode.MARKDOWN_V2)
    elif message.forward_from:
        user = message.forward_from
        age_estimation = estimate_account_age(user.id)
        scam_analysis = await analyze_scam_potential(user, context.bot, user.id)
        response = (
            f"👤 **የተጠቃሚ መረጃ**\n\n"
            f"**ስም:** {user.first_name} {user.last_name or ''}\n"
            f"**Username:** @{user.username if user.username else 'የለውም'}\n"
            f"**User ID:** `{user.id}`\n\n---\n\n"
            f"{age_estimation}\n\n---\n\n"
            f"{scam_analysis}"
        )
        await message.reply_text(response, parse_mode=ParseMode.MARKDOWN_V2)
    elif message.forward_sender_name:
        sender_name = message.forward_sender_name
        response = (
            f"🚫 **መረጃው ተደብቋል**\n\n"
            f"ይህ ተጠቃሚ (`{sender_name}`) አካውንታቸው `forward` ሲደረግ እንዳይታይ አድርገዋል።"
        )
        await message.reply_text(response, parse_mode=ParseMode.MARKDOWN_V2)

# --------------------- ለ Vercel የተስተካከለው ክፍል ---------------------

async def main_async():
    """ይህ ተግባር አፕሊኬሽኑን ገንብቶ ለስራ ዝግጁ ያደርገዋል"""
    ptb_app = Application.builder().token(TOKEN).build()
    
    # ትዕዛዞችን መጨመር
    ptb_app.add_handler(CommandHandler("start", start_command))
    ptb_app.add_handler(CommandHandler("id", id_command))
    ptb_app.add_handler(MessageHandler(filters.FORWARDED, forward_handler))

    return ptb_app

# አፕሊኬሽኑን አንድ ጊዜ ብቻ መጀመር
ptb_application = asyncio.run(main_async())

@app.route("/", methods=["POST"])
async def process_update():
    """ቴሌግራም webhook ሲልክ ይህ ተግባር ይፈጸማል"""
    update_data = request.get_json(force=True)
    update = Update.de_json(update_data, ptb_application.bot)
    
    # አፕሊኬሽኑን initialize አድርጎ መልዕክቱን ማስተናገድ
    async with ptb_application:
        await ptb_application.initialize()
        await ptb_application.process_update(update)
        await ptb_application.shutdown()
    
    return "OK", 200

# Vercel ላይ ይህ ክፍል አይሰራም፤ ለ Local Test ብቻ ነው።
if __name__ == "__main__":
    app.run(debug=True)
