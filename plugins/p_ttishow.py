from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong, PeerIdInvalid
from info import *
from database.users_chats_db import db, db2
from database.ia_filterdb import Media, Media2, db as db_stats, db2 as db2_stats
from utils import get_size, temp, get_settings, get_readable_time
from Script import script
from pyrogram.errors import ChatAdminRequired
import asyncio
import psutil
import time
from time import time
from bot import botStartTime
from logging_helper import LOGGER


"""-----------------------------------------https://t.me/SilentXBotz--------------------------------------"""

@Client.on_message(filters.new_chat_members & filters.group)
async def save_group(bot, message):
    r_j_check = [u.id for u in message.new_chat_members]
    if temp.ME in r_j_check:
        if not await db.get_chat(message.chat.id):
            total=await bot.get_chat_members_count(message.chat.id)
            r_j = message.from_user.mention if message.from_user else "Anonyme" 
            await bot.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, r_j))       
            await db.add_chat(message.chat.id, message.chat.title)
        if message.chat.id in temp.BANNED_CHATS:
            
            buttons = [[
                InlineKeyboardButton('📌 Contacter le support 📌', url=OWNER_LNK)
            ]]
            reply_markup=InlineKeyboardMarkup(buttons)
            k = await message.reply(
                text='<b>Chat non autorisé 🐞\n\nMes administrateurs ont restreint mon fonctionnement ici ! Si vous voulez en savoir plus, contactez le support.</b>',
                reply_markup=reply_markup,
            )

            try:
                await k.pin()
            except:
                pass
            await bot.leave_chat(message.chat.id)
            return
        buttons = [[
                    InlineKeyboardButton("📌 Contacter le support 📌", url=OWNER_LNK)
                  ]]
        reply_markup=InlineKeyboardMarkup(buttons)
        await message.reply_text(
            text=f"<b>Merci de m'avoir ajouté dans {message.chat.title} ❣️\n\nSi vous avez des questions ou des doutes sur mon utilisation, contactez le support.</b>",
            reply_markup=reply_markup)
        try:
            await db.connect_group(message.chat.id, message.from_user)
        except Exception as e:
            LOGGER.error(f"DB error connecting group: {e}")
    else:
        settings = await get_settings(message.chat.id)
        if settings["welcome"]:
            for u in message.new_chat_members:
                if (temp.MELCOW).get('welcome') is not None:
                    try:
                        await (temp.MELCOW['welcome']).delete()
                    except:
                        pass
                temp.MELCOW['welcome'] = await message.reply_video(
                                                 video=(MELCOW_VID),
                                                 caption=(script.MELCOW_ENG.format(u.mention, message.chat.title)),
                                                 reply_markup=InlineKeyboardMarkup(
                                                                         [[
                                                                           InlineKeyboardButton("📌 Contacter le support 📌", url=OWNER_LNK)
                                                                         ]]
                                                 ),
                                                 parse_mode=enums.ParseMode.HTML
                )
                
        if settings["auto_delete"]:
            await asyncio.sleep(600)
            await (temp.MELCOW['welcome']).delete()
                

@Client.on_message(filters.command('leave') & filters.user(ADMINS))
async def leave_a_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('Donnez-moi un ID de chat')
    chat = message.command[1]
    try:
        chat = int(chat)
    except:
        chat = chat
    try:
        buttons = [[
                  InlineKeyboardButton("📌 Contacter le support 📌", url=OWNER_LNK)
                  ]]
        reply_markup=InlineKeyboardMarkup(buttons)
        await bot.send_message(
            chat_id=chat,
            text='<b>Bonjour amis, \nMon administrateur m\'a demandé de quitter le groupe, donc je dois partir !\nSi vous voulez m\'ajouter à nouveau, contactez le support.</b>',
            reply_markup=reply_markup,
        )

        await bot.leave_chat(chat)
        await message.reply(f"Chat quitté `{chat}`")
    except Exception as e:
        await message.reply(f'Erreur - {e}')

@Client.on_message(filters.command('disable') & filters.user(ADMINS))
async def disable_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('Donnez-moi un ID de chat')
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "Aucune raison fournie"
    try:
        chat_ = int(chat)
    except:
        return await message.reply('Donnez-moi un ID de chat valide')
    cha_t = await db.get_chat(int(chat_))
    if not cha_t:
        return await message.reply("Chat non trouvé dans la base de données")
    if cha_t['is_disabled']:
        return await message.reply(f"Ce chat est déjà désactivé:\nRaison-<code> {cha_t['reason']} </code>")
    await db.disable_chat(int(chat_), reason)
    temp.BANNED_CHATS.append(int(chat_))
    await message.reply('Chat désactivé avec succès')
    try:
        buttons = [[
            InlineKeyboardButton('📌 Contacter le support 📌', url=OWNER_LNK)
        ]]
        reply_markup=InlineKeyboardMarkup(buttons)
        await bot.send_message(
            chat_id=chat_, 
            text=f'<b>Bonjour amis, \nMon administrateur m\'a demandé de quitter le groupe, donc je dois partir ! \nSi vous voulez m\'ajouter à nouveau, contactez le support..</b> \nRaison : <code>{reason}</code>',
            reply_markup=reply_markup)
        await bot.leave_chat(chat_)
    except Exception as e:
        await message.reply(f"Erreur - {e}")


@Client.on_message(filters.command('enable') & filters.user(ADMINS))
async def re_enable_chat(bot, message):
    if len(message.command) == 1:
        return await message.reply('Donnez-moi un ID de chat')
    chat = message.command[1]
    try:
        chat_ = int(chat)
    except:
        return await message.reply('Donnez-moi un ID de chat valide')
    sts = await db.get_chat(int(chat))
    if not sts:
        return await message.reply("Chat non trouvé dans la base de données !")
    if not sts.get('is_disabled'):
        return await message.reply('Ce chat n\'est pas encore désactivé.')
    await db.re_enable_chat(int(chat_))
    temp.BANNED_CHATS.remove(int(chat_))
    await message.reply("Chat réactivé avec succès")

@Client.on_message(filters.command('stats') & filters.user(ADMINS))
async def get_stats(bot, message):
    try:
        SilentXBotz = await message.reply('Accès aux détails du statut...')
        total_users = await db.total_users_count()
        totl_chats = await db.total_chat_count()
        premium = await db.all_premium_users()
        file1 = await Media.count_documents()
        DB_SIZE = 512 * 1024 * 1024
        dbstats = await db_stats.command("dbStats")
        db_size = dbstats['dataSize']
        free = DB_SIZE - db_size
        uptime = get_readable_time(time() - botStartTime)
        ram = psutil.virtual_memory().percent
        cpu = psutil.cpu_percent()
        if MULTIPLE_DB == False:
            await SilentXBotz.edit(script.STATUS_TXT.format(
                total_users, totl_chats, premium, file1, get_size(db_size), get_size(free), uptime, ram, cpu))                                               
            return
        file2 = await Media2.count_documents()
        db2stats = await db2_stats.command("dbStats")
        db2_size = db2stats['dataSize']
        free2 = DB_SIZE - db2_size
        await SilentXBotz.edit(script.MULTI_STATUS_TXT.format(
            total_users, totl_chats, premium, file1, get_size(db_size), get_size(free),
            file2, get_size(db2_size), get_size(free2), uptime, ram, cpu, (int(file1) + int(file2))
        ))
    except Exception as e:
        LOGGER.error(e)
        

@Client.on_message(filters.command('invite') & filters.user(ADMINS))
async def gen_invite(bot, message):
    if len(message.command) == 1:
        return await message.reply('Donnez-moi un ID de chat')
    chat = message.command[1]
    try:
        chat = int(chat)
    except:
        return await message.reply('Donnez-moi un ID de chat valide')
    try:
        link = await bot.create_chat_invite_link(chat)
    except ChatAdminRequired:
        return await message.reply("Échec de la génération du lien d'invitation, je n'ai pas les droits suffisants")
    except Exception as e:
        return await message.reply(f'Erreur {e}')
    await message.reply(f'Voici votre lien d\'invitation {link.invite_link}')

@Client.on_message(filters.command('ban') & filters.user(ADMINS))
async def ban_a_user(bot, message):
    if len(message.command) == 1:
        return await message.reply('Donnez-moi un ID utilisateur / nom d\'utilisateur')
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "Aucune raison fournie"
    try:
        chat = int(chat)
    except:
        pass
    try:
        k = await bot.get_users(chat)
    except PeerIdInvalid:
        return await message.reply("Cet utilisateur est invalide, assurez-vous que je l'ai rencontré auparavant.")
    except IndexError:
        return await message.reply("Ce pourrait être un canal, assurez-vous que c'est un utilisateur.")
    except Exception as e:
        return await message.reply(f'Erreur - {e}')
    else:
        jar = await db.get_ban_status(k.id)
        if jar['is_banned']:
            return await message.reply(f"{k.mention} est déjà banni\nRaison: {jar['ban_reason']}")
        await db.ban_user(k.id, reason)
        temp.BANNED_USERS.append(k.id)
        await message.reply(f"{k.mention} banni avec succès")
    
@Client.on_message(filters.command('unban') & filters.user(ADMINS))
async def unban_a_user(bot, message):
    if len(message.command) == 1:
        return await message.reply('Donnez-moi un ID utilisateur / nom d\'utilisateur')
    r = message.text.split(None)
    if len(r) > 2:
        reason = message.text.split(None, 2)[2]
        chat = message.text.split(None, 2)[1]
    else:
        chat = message.command[1]
        reason = "Aucune raison fournie"
    try:
        chat = int(chat)
    except:
        pass
    try:
        k = await bot.get_users(chat)
    except PeerIdInvalid:
        return await message.reply("Cet utilisateur est invalide, assurez-vous que je l'ai rencontré auparavant.")
    except IndexError:
        return await message.reply("Ce pourrait être un canal, assurez-vous que c'est un utilisateur.")
    except Exception as e:
        return await message.reply(f'Erreur - {e}')
    else:
        jar = await db.get_ban_status(k.id)
        if not jar['is_banned']:
            return await message.reply(f"{k.mention} n'est pas encore banni.")
        await db.remove_ban(k.id)
        temp.BANNED_USERS.remove(k.id)
        await message.reply(f"{k.mention} débanni avec succès")
 
@Client.on_message(filters.command('users') & filters.user(ADMINS))
async def list_users(bot, message):
    raju = await message.reply('Obtention de la liste des utilisateurs')
    users = await db.get_all_users()
    out = "Les utilisateurs enregistrés dans la base de données sont:\n\n"
    async for user in users:
        out += f"<a href=tg://user?id={user['id']}>{user['name']}</a>"
        if user['ban_status']['is_banned']:
            out += '( Utilisateur banni )'
        out += '\n'
    try:
        await raju.edit_text(out)
    except MessageTooLong:
        with open('users.txt', 'w+') as outfile:
            outfile.write(out)
        await message.reply_document('users.txt', caption="Liste des utilisateurs")

@Client.on_message(filters.command('chats') & filters.user(ADMINS))
async def list_chats(bot, message):
    raju = await message.reply('Obtention de la liste des chats')
    chats = await db.get_all_chats()
    out = "Les chats enregistrés dans la base de données sont:\n\n"
    async for chat in chats:
        out += f"**Titre:** `{chat['title']}`\n**- ID:** `{chat['id']}`"
        if chat['chat_status']['is_disabled']:
            out += '( Chat désactivé )'
        out += '\n'
    try:
        await raju.edit_text(out)
    except MessageTooLong:
        with open('chats.txt', 'w+') as outfile:
            outfile.write(out)
        await message.reply_document('chats.txt', caption="Liste des chats")