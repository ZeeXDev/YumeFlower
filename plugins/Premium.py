from datetime import timedelta
import pytz
import datetime, time
from Script import script 
from info import *
from utils import get_seconds, temp
from database.users_chats_db import db 
import asyncio
from pyrogram import Client, filters 
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong
from pyrogram.types import *
from logging_helper import LOGGER

@Client.on_message(filters.command("remove_premium") & filters.user(ADMINS))
async def remove_premium(client, message):
    if len(message.command) == 2:
        user_id = int(message.command[1])
        user = await client.get_users(user_id)
        if await db.remove_premium_access(user_id):
            await message.reply_text("Utilisateur retiré avec succès !")
            await client.send_message(
                chat_id=user_id,
                text=f"<b>Salut {user.mention},\n\nVotre Accès Premium A Été Retiré. Merci D'avoir Utilisé Notre Service 😊. Cliquez Sur /plan Pour Vérifier Nos Autres Plans.\n\n<blockquote>आपका Premium Access हटा दिया गया है। हमारी सेवा का उपयोग करने के लिए धन्यवाद 🥳 हमारी अन्य योजनाओं की जाँच करने के लिए /plan पर क्लिक करें ।</blockquote></b>"
            )
        else:
            await message.reply_text("Impossible de retirer l'utilisateur !\nÊtes-vous sûr, c'était un ID utilisateur premium ?")
    else:
        await message.reply_text("Usage : /remove_premium user_id") 

@Client.on_message(filters.command("myplan"))
async def myplan(client, message):
    try:
        user = message.from_user.mention 
        user_id = message.from_user.id
        data = await db.get_user(message.from_user.id) 
        if data and data.get("expiry_time"):
            expiry = data.get("expiry_time") 
            expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
            expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ Heure d'expiration : %I:%M:%S %p")            
            current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
            time_left = expiry_ist - current_time
            days = time_left.days
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_left_str = f"{days} jours, {hours} heures, {minutes} minutes"
            await message.reply_text(f"⚜️ Données utilisateur premium :\n\n👤 Utilisateur : {user}\n⚡ ID utilisateur : <code>{user_id}</code>\n⏰ Temps restant : {time_left_str}\n⌛️ Date d'expiration : {expiry_str_in_ist}")   
        else:
            await message.reply_text(f"<b>Salut {user},\n\nVous n'avez pas de plan premium actif. Achetez notre abonnement pour utiliser les avantages premium.<b>",
	    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("• Vérifier les plans premium •", callback_data='buy')]]))
    except Exception as e:
        LOGGER.info(e)

@Client.on_message(filters.command("get_premium") & filters.user(ADMINS))
async def get_premium(client, message):
    if len(message.command) == 2:
        user_id = int(message.command[1])
        user = await client.get_users(user_id)
        data = await db.get_user(user_id)  
        if data and data.get("expiry_time"):
            expiry = data.get("expiry_time") 
            expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
            expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ Heure d'expiration : %I:%M:%S %p")            
            current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
            time_left = expiry_ist - current_time
            days = time_left.days
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_left_str = f"{days} jours, {hours} heures, {minutes} minutes"
            await message.reply_text(f"⚜️ Données utilisateur premium :\n\n👤 Utilisateur : {user.mention}\n⚡ ID utilisateur : <code>{user_id}</code>\n⏰ Temps restant : {time_left_str}\n⌛️ Date d'expiration : {expiry_str_in_ist}")
        else:
            await message.reply_text("Aucune donnée premium trouvée dans la base de données !")
    else:
        await message.reply_text("Usage : /get_premium user_id")

@Client.on_message(filters.command("add_premium") & filters.user(ADMINS))
async def give_premium_cmd_handler(client, message):
    if len(message.command) == 4:
        time_zone = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        current_time = time_zone.strftime("%d-%m-%Y\n⏱️ Heure d'adhésion : %I:%M:%S %p") 
        user_id = int(message.command[1])  
        user = await client.get_users(user_id)
        time = message.command[2]+" "+message.command[3]
        seconds = await get_seconds(time)
        if seconds > 0:
            expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            user_data = {"id": user_id, "expiry_time": expiry_time}  
            await db.update_user(user_data) 
            data = await db.get_user(user_id)
            expiry = data.get("expiry_time")   
            expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ Heure d'expiration : %I:%M:%S %p")         
            await message.reply_text(f"Premium ajouté avec succès ✅\n\n👤 Utilisateur : {user.mention}\n⚡ ID utilisateur : <code>{user_id}</code>\n⏰ Accès premium : <code>{time}</code>\n\n⏳ Date d'adhésion : {current_time}\n\n⌛️ Date d'expiration : {expiry_str_in_ist}", disable_web_page_preview=True)
            await client.send_message(
                chat_id=user_id,
                text=f"👋 Salut {user.mention},\nMerci d'avoir acheté premium.\nProfitez-en !! ✨🎉\n\n⏰ Accès premium : <code>{time}</code>\n⏳ Date d'adhésion : {current_time}\n\n⌛️ Date d'expiration : {expiry_str_in_ist}", disable_web_page_preview=True              
            )    
            await client.send_message(PREMIUM_LOGS, text=f"#Premium_Ajouté\n\n👤 Utilisateur : {user.mention}\n⚡ ID utilisateur : <code>{user_id}</code>\n⏰ Accès premium : <code>{time}</code>\n\n⏳ Date d'adhésion : {current_time}\n\n⌛️ Date d'expiration : {expiry_str_in_ist}", disable_web_page_preview=True)
                    
        else:
            await message.reply_text("Format de temps invalide. Veuillez utiliser '1 day pour jours', '1 hour pour heures', ou '1 min pour minutes', ou '1 month pour mois' ou '1 year pour année'")
    else:
        await message.reply_text("Usage : /add_premium user_id temps (ex. '1 day pour jours', '1 hour pour heures', ou '1 min pour minutes', ou '1 month pour mois' ou '1 year pour année')")

@Client.on_message(filters.command("premium_users") & filters.user(ADMINS))
async def premium_user(client, message):
    aa = await message.reply_text("<i>Récupération...</i>")
    new = f" Liste des utilisateurs premium :\n\n"
    user_count = 1
    users = await db.get_all_users()
    async for user in users:
        data = await db.get_user(user['id'])
        if data and data.get("expiry_time"):
            expiry = data.get("expiry_time") 
            expiry_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata"))
            expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ Heure d'expiration : %I:%M:%S %p")            
            current_time = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
            time_left = expiry_ist - current_time
            days = time_left.days
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_left_str = f"{days} jours, {hours} heures, {minutes} minutes"	 
            new += f"{user_count}. {(await client.get_users(user['id'])).mention}\n👤 ID utilisateur : {user['id']}\n⏳ Date d'expiration : {expiry_str_in_ist}\n⏰ Temps restant : {time_left_str}\n"
            user_count += 1
        else:
            pass
    try:    
        await aa.edit_text(new)
    except MessageTooLong:
        with open('usersplan.txt', 'w+') as outfile:
            outfile.write(new)
        await message.reply_document('usersplan.txt', caption="Utilisateurs payants:")

@Client.on_message(filters.command("plan"))
async def plan(client, message):
    user_id = message.from_user.id 
    users = message.from_user.mention
    log_message = f"<b><u>🚫 Cet utilisateur a essayé de vérifier /plan</u> {temp.B_LINK}\n\n- ID - `{user_id}`\n- Nom - {users}</b>" 
    btn = [[
            InlineKeyboardButton('• Acheter premium •', callback_data='buy'),           
    ],[                
	    InlineKeyboardButton('• Parrainer des amis', callback_data='reffff'),                
	    InlineKeyboardButton('Essai gratuit •', callback_data='free')        
    ],[            
            InlineKeyboardButton('🚫 Fermer 🚫', callback_data='close_data')
    ]]
    msg = await message.reply_photo(photo="https://graph.org/file/86da2027469565b5873d6.jpg", caption=script.BPREMIUM_TXT, reply_markup=InlineKeyboardMarkup(btn))
    await client.send_message(PREMIUM_LOGS, log_message)
    await asyncio.sleep(300)
    await msg.delete()
    await message.delete()


# Méthode de paiement par étoiles Telegram 
# Crédit - https://github.com/NBBotz 
# Crédit - https://telegram.me/SilentXBotz

@Client.on_callback_query(filters.regex(r"buy_\d+"))
async def premium_button(client, callback_query: CallbackQuery):
    try:
        amount = int(callback_query.data.split("_")[1])
        if amount in STAR_PREMIUM_PLANS:
            try:
                buttons = [[	
                    InlineKeyboardButton("Annuler 🚫", callback_data="cancel_star_premium"),		    				
                ]]
                reply_markup = InlineKeyboardMarkup(buttons)
                await client.send_invoice(
                    chat_id=callback_query.message.chat.id,
                    title="Abonnement Premium",
                    description=f"Payez {amount} Étoiles Et Obtenez Premium Pour {STAR_PREMIUM_PLANS[amount]}",
                    payload=f"silentxpremium_{amount}",
                    currency="XTR",
                    prices=[
                        LabeledPrice(
                            label="Abonnement Premium", 
                            amount=amount
                        ) 
                    ],
                    reply_markup=reply_markup
                )
                await callback_query.answer()
            except Exception as e:
                LOGGER.error(f"Error sending invoice: {e}")
                await callback_query.answer("🚫 Erreur de traitement de votre paiement. Réessayez.", show_alert=True)
        else:
            await callback_query.answer("⚠️ Forfait premium invalide.", show_alert=True)
    except Exception as e:
        LOGGER.error(f"Error In buy_ - {e}")
 
@Client.on_pre_checkout_query()
async def pre_checkout_handler(client, query: PreCheckoutQuery):
    try:
        if query.payload.startswith("silentxpremium_"):
            await query.answer(success=True)
        else:
            await query.answer(success=False, error_message="⚠️ Type d'achat invalide.", show_alert=True)
    except Exception as e:
        LOGGER.error(f"Pre-checkout error: {e}")
        await query.answer(success=False, error_message="🚫 Une erreur inattendue s'est produite." , show_alert=True)

@Client.on_message(filters.successful_payment)
async def successful_premium_payment(client, message):
    try:
        amount = int(message.successful_payment.total_amount)
        user_id = message.from_user.id
        time_zone = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        current_time = time_zone.strftime("%d-%m-%Y | %I:%M:%S %p") 
        if amount in STAR_PREMIUM_PLANS:
            time = STAR_PREMIUM_PLANS[amount]
            seconds = await get_seconds(time)
            if seconds > 0:
                expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
                user_data = {"id": user_id, "expiry_time": expiry_time}
                await db.update_user(user_data)
                data = await db.get_user(user_id)
                expiry = data.get("expiry_time")
                expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y | %I:%M:%S %p")    
                await message.reply(text=f"Merci d'avoir acheté le service premium avec des étoiles ✅\n\nDurée d'abonnement - {time}\nExpire le - {expiry_str_in_ist}", disable_web_page_preview=True)                
                await client.send_message(PREMIUM_LOGS, text=f"#Achat_Premium_Étoiles\n\n👤 Utilisateur - {user.mention}\n\n⚡ ID utilisateur - <code>{user_id}</code>\n\n🚫 Paiement étoiles - {amount}⭐\n\n⏰ Accès premium - {time}\n\n⌛️ Date d'adhésion - {current_time}\n\n⌛️ Date d'expiration - {expiry_str_in_ist}", disable_web_page_preview=True)
            else:
                await message.reply("⚠️ Durée premium invalide.")
        else:
            await message.reply("⚠️ Forfait premium invalide.")
    except Exception as e:
        LOGGER.error(f"Error Processing Premium Payment: {e}")
        await message.reply("✅ Merci pour votre paiement ! (Erreur d'enregistrement des détails)")

@Client.on_callback_query(filters.regex("cancel_star_premium"))
async def cancel_premium(client, callback_query: CallbackQuery):
    await callback_query.message.delete()