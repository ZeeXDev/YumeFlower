# This code has been modified by @Safaridev
import re
import time
import pytz
import asyncio
import hashlib
import random
import string
from os import environ
from info import ADMINS, PREMIUM_LOGS
from datetime import datetime, timedelta
from pyrogram import Client, filters
from database.users_chats_db import db
from utils import *

def hash_code(code):
    return hashlib.sha256(code.encode()).hexdigest()

async def generate_code(duration_str):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    kolkata_tz = pytz.timezone("Asia/Kolkata")
    created_at = datetime.now(tz=kolkata_tz) 

    await db.codes.insert_one({
        "code_hash": hash_code(code),
        "duration": duration_str,
        "used": False,
        "created_at": created_at,
        "original_code": code
    })
    return code
        
async def parse_duration(duration_str):
    pattern = r'(\d+)\s*(minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)'
    match = re.match(pattern, duration_str.lower())

    if not match:
        return None  

    value, unit = match.groups()
    value = int(value)

    if "minute" in unit:
        return value * 60
    elif "hour" in unit:
        return value * 60 * 60
    elif "day" in unit:
        return value * 24 * 60 * 60
    elif "week" in unit:
        return value * 7 * 24 * 60 * 60
    elif "month" in unit:
        return value * 30 * 24 * 60 * 60
    elif "year" in unit:
        return value * 365 * 24 * 60 * 60

    return None

@Client.on_message(filters.command("add_redeem") & filters.user(ADMINS))
async def generate_code_cmd(client, message):
    if len(message.command) == 2:
        duration_str = message.command[1]
        premium_duration_seconds = await parse_duration(duration_str)
        if premium_duration_seconds is not None:
            token = await generate_code(duration_str)
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔑 Utiliser maintenant 🔥", url=f"https://t.me/{temp.U_NAME}")]])
            await message.reply_text(f"✅ Code généré avec succès ♻️\n\n🔑 Code : `{token}`\n⌛ Validité : {duration_str}\n\nUtilisation : `/redeem {token}`\n\nNote : Un seul utilisateur peut l'utiliser", reply_markup=keyboard)
                                       
        else:
            await message.reply_text("❌ Format de durée invalide. Veuillez entrer une durée valide comme '1minute', '1hours', '1days', '1months', '1years', etc.")
    else:
        await message.reply_text("Usage : /code 1month")

@Client.on_message(filters.command("redeem"))
async def redeem_code_cmd(client, message):
    if len(message.command) == 2:
        code = message.command[1]
        user_id = message.from_user.id

        if not await db.has_premium_access(user_id):
            code_data = await db.codes.find_one({"code_hash": hash_code(code)})
            if code_data:
                if code_data['used']:
                    await message.reply_text(f"🚫 Ce code a déjà été utilisé 🚫.")
                    return
                premium_duration_seconds = await parse_duration(code_data['duration'])
                if premium_duration_seconds is not None:
                    new_expiry = datetime.now() + timedelta(seconds=premium_duration_seconds)
                    user_data = {"id": user_id, "expiry_time": new_expiry}
                    await db.update_user(user_data)
                    await db.codes.update_one({"_id": code_data["_id"]}, {"$set": {"used": True, "user_id": user_id}})
                    expiry_str_in_ist = new_expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("⌛️ Date d'expiration : %d-%m-%Y\n⏱️ Heure d'expiration : %I:%M:%S %p")
                    await message.reply_text(f"🎉 Code utilisé avec succès !\nVous avez maintenant un accès premium jusqu'à :\n\n✨ Durée : {code_data['duration']}\n{expiry_str_in_ist}")
                else:
                    await message.reply_text("🚫 Durée invalide dans le code.")
            else:
                await message.reply_text("🚫 Code invalide ou expiré.")
        else:
            await message.reply_text("❌ Vous avez déjà un accès premium.")
    else:
        await message.reply_text("Usage : /redeem <code>")

@Client.on_message(filters.command("clearcodes") & filters.user(ADMINS))
async def clear_codes_cmd(client, message):
    result = await db.codes.delete_many({})
    if result.deleted_count > 0:
        await message.reply_text(f"✅ Tous les {result.deleted_count} codes ont été supprimés avec succès.")
    else:
        await message.reply_text("⚠️ Aucun code trouvé à supprimer.")

@Client.on_message(filters.command("allcodes") & filters.user(ADMINS))
async def all_codes_cmd(client, message):
    all_codes = await db.codes.find({}).to_list(length=None)
    if not all_codes:
        await message.reply_text("⚠️ Aucun code disponible.")
        return

    codes_info = "📝 **Détails des codes générés :**\n\n"
    for code_data in all_codes:
        original_code = code_data.get("original_code", "Inconnu") 
        duration = code_data.get("duration", "Inconnu")
        user_id = code_data.get("user_id")
        used = "Oui ✅" if code_data.get("used", False) else "Non ⭕"
        created_at = code_data["created_at"].astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M %p")
        if user_id:
            user = await client.get_users(user_id)
            user_name = user.first_name if user.first_name else "Utilisateur inconnu"
            user_mention = f"[{user_name}](tg://user?id={user_id})"
        else:
            user_mention = "Non utilisé"
        
        codes_info += f"**🔑 Code** : `{original_code}`\n"
        codes_info += f"**⌛ Durée** : {duration}\n"
        codes_info += f"**‼ Utilisé** : {used}\n"
        codes_info += f"**🕓 Créé le** : {created_at}\n"
        codes_info += f"**🙎 ID utilisateur** : {user_mention}\n\n"


    for chunk in [codes_info[i:i + 4096] for i in range(0, len(codes_info), 4096)]:
        await message.reply_text(chunk)