# -*- coding: utf-8 -*-
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                                               #
#        ሁለገብ የቴሌግራም መረጃ አግኚ ቦት (Info Bot)               #
#                 V.6 - የመጨረሻ የተረጋጋ እትም                     #
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
    return f"📅 **የተከፈተበት ጊዜ:** በግምት በ {year_created} ወይም ከዚያ በኋላ።"

async def analyze_scam_potential(user: 'User', bot_instance: Bot, user_id: int) -> str:
    """የማጭበርበር ስጋትን በበለጠ ዝርዝር ይመረምራል"""
    warnings = []
    score = 0

    try:
        profile_photos = await bot_instance.get_user_profile_photos(user_id, limit=1)
        if profile_photos.total_count == 0:
            warnings.append("• 🖼️ ፕሮፋይል ፎቶ የለውም።")
            score += 2
    except Exception as e:
        logger.warning(f"Could not fetch profile photos for {user_id}: {e}")

    if not user.username:
        warnings.append("• ✍️ Username አልተቀመጠለትም።")
        score += 1

    try:
        full_user = await bot_instance.get_chat(user_id)
        bio = full_user.bio
        full_name = full_user.full_name.lower()
        
        if not bio:
            warnings.append("• 📝 ባዮ (Bio) አልተጻፈም።")
            score += 1
        else:
            suspicious_bio_keywords = ['crypto', 'investment', 'forex', 'manager', 'guaranteed profit', 'investor', 'cashapp']
            for keyword in suspicious_bio_keywords:
                if keyword in bio.lower():
                    warnings.append(f"• ☣️ ባዮ '{keyword}' የሚል አጠራጣሪ ቃል ይዟል።")
                    score += 3
                    break

        suspicious_name_keywords = ['admin', 'support', 'telegram', 'premium', 'service', 'account']
        for keyword in suspicious_name_keywords:
            if keyword in full_name:
                warnings.append(f"• 📛 ስሙ '{keyword.capitalize()}' የሚል አጠራጣሪ ቃል ይዟል።")
                score += 3
    except Exception as e:
        logger.warning(f"Could not fetch full user profile for {user_id}: {e}")

    if not warnings:
        return "✅ **የደህንነት ትንታኔ:**\nምንም ቀጥተኛ አጠራጣሪ ነገር አልተገኘም።"
    
    summary = ""
    if score >= 5:
        summary = "🔴 **ከፍተኛ ጥንቃቄ ያድርጉ**"
    elif score >= 3:
        summary = "🟡 **መካከለኛ ጥንቃቄ ያድርጉ**"
    else:
        summary = "🟢 **ዝቅተኛ ስጋት**"

    return f"⚠️ **የደህንነት ትንታኔ:** {summary}\n\n" + "\n".join(warnings)


async def get_user_full_info(user_to_check, bot_instance, reply_message):
    """የተጠቃሚን ሙሉ መረጃ አቀናብሮ ይመልሳል"""
    age_estimation = estimate_account_age(user_to_check.id)
    scam_analysis = await analyze_scam_potential(user_to_check, bot_instance, user_to_check.id)
    response = (
        f"👤 **የተጠቃሚ መረጃ**\n\n"
        f"**ስም:** {user_to_check.first_name} {user_to_check.last_name or ''}\n"
        f"**Username:** @{user_to_check.username if user_to_check.username else 'የለውም'}\n"
        f"**User ID:** `{user_to_check.id}`\n\n"
        f"{age_estimation}\n\n"
        f"---\n\n"
        f"{scam_analysis}"
    )
    await reply_message.reply_text(response, parse_mode=ParseMode.MARKDOWN_V2)

# --------------------------- የቦት ትዕዛዝ እና ምላሾች ---------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    welcome_message = (
        f"👋 ሰላም {user.mention_html()}!\n\n"
        "እኔ ሁለገብ መረጃ አግኚ ቦት ነኝ። መረጃ ለማግኘት ከሚከተሉት አንዱን ይጠቀሙ:\n\n"
        "1️⃣ **Forward በማድረግ:**\n"
        "   - ከአንድ ሰው ወይም ቻናል የተላከን መልዕክት ወደ እኔ `Forward` ያድርጉ።\n\n"
        "2️⃣ **Reply በማድረግ:**\n"
        "   - የማንኛውንም ሰው መልዕክት `Reply` አድርገው `/info` ብለው ይላኩ።\n\n"
        "3️⃣ **/id ትዕዛዝ:**\n"
        "   - የራስዎን ወይም የግሩፑን ID ለማወቅ `/id` ብለው ይላኩ።"
    )
    await update.message.reply_html(welcome_message)

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = f"👤 **የእርስዎ User ID:** `{user.id}`\n"
    if chat.id != user.id:
        message += f"💬 **የዚህ ግሩፕ/ቻናል ID:** `{chat.id}`"
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply የተደረገለት ተጠቃሚን መረጃ ያሳያል"""
    if not update.message.reply_to_message:
        await update.message.reply_text("እባክዎ ይህንን ትዕዛዝ ለመጠቀም የአንድን ሰው መልዕክት Reply ያድርጉ።")
        return
    
    user_to_check = update.message.reply_to_message.from_user
    await get_user_full_info(user_to_check, context.bot, update.message)

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
        user_to_check = message.forward_from
        await get_user_full_info(user_to_check, context.bot, message)
    elif message.forward_sender_name:
        sender_name = message.forward_sender_name
        response = (
            f"🚫 **መረጃው ተደብቋል**\n\n"
            f"ይህ ተጠቃሚ (`{sender_name}`) አካውንታቸው `forward` ሲደረግ እንዳይታይ አድርገዋል።"
        )
        await message.reply_text(response, parse_mode=ParseMode.MARKDOWN_V2)

# --------------------- ለ Vercel የተስተካከለው ክፍል ---------------------
# የቦቱን አፕሊኬሽን አንድ ጊዜ ብቻ መገንባት
ptb_app = Application.builder().token(TOKEN).build()
ptb_app.add_handler(CommandHandler("start", start_command))
ptb_app.add_handler(CommandHandler("id", id_command))
ptb_app.add_handler(CommandHandler("info", info_command))
ptb_app.add_handler(MessageHandler(filters.FORWARDED, forward_handler))


@app.route("/", methods=["POST"])
async def process_update():
    """ቴሌግራም webhook ሲልክ ይህ ተግባር ይፈጸማል"""
    try:
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, ptb_app.bot)
        
        # አፕሊኬሽኑን አስጀምሮ መልዕክቱን ማስተናገድ
        async with ptb_app:
            await ptb_app.process_update(update)
            
    except Exception as e:
        logger.error(f"An error occurred in process_update: {e}")
    
    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True)

