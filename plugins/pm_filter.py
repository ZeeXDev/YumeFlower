import asyncio
import re
import ast
import math
import random
import pytz
from datetime import datetime, timedelta, date, time
lock = asyncio.Lock()
from database.users_chats_db import db
from database.refer import referdb
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from info import *
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, WebAppInfo
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import *
from fuzzywuzzy import process
from database.users_chats_db import db
from database.ia_filterdb import Media, Media2, get_file_details, get_search_results, get_bad_files
from logging_helper import LOGGER
from urllib.parse import quote_plus
from Lucia.util.file_properties import get_name, get_hash, get_media_file_size
from database.topdb import silentdb
import requests
import string
import tracemalloc

tracemalloc.start()

TIMEZONE = "Asia/Kolkata"
BUTTON = {}
BUTTONS = {}
FRESH = {}
SPELL_CHECK = {}


@Client.on_message(filters.group & filters.text & filters.incoming)
async def give_filter(client, message):
    bot_id = client.me.id
    if EMOJI_MODE:
        try:
            await message.react(emoji=random.choice(REACTIONS))
        except Exception:
            pass
    maintenance_mode = await db.get_maintenance_status(bot_id)
    if maintenance_mode and message.from_user.id not in ADMINS:
        await message.reply_text(f"Je suis actuellement en maintenance 🛠️. Je serai de retour bientôt 🔜", disable_web_page_preview=True)
        return
    await silentdb.update_top_messages(message.from_user.id, message.text)
    if message.chat.id != SUPPORT_CHAT_ID:
        settings = await get_settings(message.chat.id)
        if settings['auto_ffilter']:
            if re.search(r'https?://\S+|www\.\S+|t\.me/\S+', message.text):
                if await is_check_admin(client, message.chat.id, message.from_user.id):
                    return
                return await message.delete()   
            await auto_filter(client, message)
    else:
        search = message.text
        temp_files, temp_offset, total_results = await get_search_results(chat_id=message.chat.id, query=search.lower(), offset=0, filter=True)
        if total_results == 0:
            return
        else:
            return await message.reply_text(f"<b>Salut {message.from_user.mention},\n\nVotre demande est déjà disponible ✅\n\n📂 Fichiers trouvés : {str(total_results)}\n🔍 Recherche :</b> <code>{search}</code>\n\n<b>‼️ Ceci est un <u>groupe de support</u> donc vous ne pouvez pas obtenir de fichiers ici...\n\n📝 Recherchez ici : 👇</b>",   
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔍 Rejoignez et recherchez ici 🔎", url=GRP_LNK)]]))


@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_text(bot, message):
    bot_id = bot.me.id
    content = message.text
    user = message.from_user.first_name
    user_id = message.from_user.id
    if EMOJI_MODE:
        try:
            await message.react(emoji=random.choice(REACTIONS))
        except Exception:
            pass
    maintenance_mode = await db.get_maintenance_status(bot_id)
    if maintenance_mode and message.from_user.id not in ADMINS:
        await message.reply_text(f"Je suis actuellement en maintenance 🛠️. Je serai de retour bientôt 🔜", disable_web_page_preview=True)
        return
    if content.startswith(("/", "#")):
        return  
    try:
        await silentdb.update_top_messages(user_id, content)
        pm_search = await db.pm_search_status(bot_id)
        if pm_search:
            await auto_filter(bot, message)
        else:
            await message.reply_text(
             text=f"<b><i>Je ne travaille pas ici 🚫.\nRejoignez mon groupe depuis le bouton ci-dessous et recherchez là-bas !</i></b>",   
             reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📝 Recherchez ici ", url=GRP_LNK)]])
            )
    except Exception as e:
        LOGGER.error(f"An error occurred: {str(e)}")


@Client.on_callback_query(filters.regex(r"^reffff"))
async def refercall(bot, query):
    btn = [[
        InlineKeyboardButton('lien d\'invitation', url=f'https://telegram.me/share/url?url=https://t.me/{bot.me.username}?start=reff_{query.from_user.id}&text=Hello%21%20Experience%20a%20bot%20that%20offers%20a%20vast%20library%20of%20unlimited%20movies%20and%20series.%20%F0%9F%98%83'),
        InlineKeyboardButton(f'⏳ {referdb.get_refer_points(query.from_user.id)}', callback_data='ref_point'),
        InlineKeyboardButton('retour', callback_data='premium')
    ]]
    reply_markup = InlineKeyboardMarkup(btn)
    await bot.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto("https://graph.org/file/1a2e64aee3d4d10edd930.jpg")
        )
    await query.message.edit_text(
        text=f'Voici votre lien de parrainage :\n\nhttps://t.me/{bot.me.username}?start=reff_{query.from_user.id}\n\nPartagez ce lien avec vos amis, chaque fois qu\'ils rejoignent, vous obtiendrez 10 points de parrainage et après 100 points vous obtiendrez 1 mois d\'abonnement premium.',
        reply_markup=reply_markup,
        parse_mode=enums.ParseMode.HTML
        )
    await query.answer()
	
async def build_pagination_buttons(btn, total_results, current_offset, next_offset, req, key, settings):
    limit = 10 if settings.get('max_btn') else int(MAX_B_TN)
    total_pages = math.ceil(total_results / limit)
    current_page = math.ceil(current_offset / limit) + 1
    pagination_row = []
    if current_offset > 0:
        prev_offset = max(0, current_offset - limit)
        pagination_row.append(InlineKeyboardButton("⋞ précédent", callback_data=f"next_{req}_{key}_{prev_offset}"))
    pagination_row.append(InlineKeyboardButton(f"{current_page} / {total_pages}", callback_data="pages"))
    if next_offset is not None and next_offset != 0 and next_offset < total_results:
         pagination_row.append(InlineKeyboardButton("suivant ⋟", callback_data=f"next_{req}_{key}_{next_offset}"))
    elif next_offset == 0 and current_offset + limit < total_results:
         pass
    if len(pagination_row) == 1 and pagination_row[0].text.startswith(str(current_page)):
         if total_pages > 1:
             btn.append(pagination_row)
         else:
             btn.append([InlineKeyboardButton(text="↭ aucune autre page disponible ↭", callback_data="pages")])
    else:
         btn.append(pagination_row)

async def generic_filter_handler(client, query, key, offset, search_query):
    files, n_offset, total_results = await get_search_results(query.message.chat.id, search_query, offset=offset, filter=True)
    if not files:
        await query.answer("🚫 Aucun fichier trouvé 🚫", show_alert=1)
        return
    temp.GETALL[key] = files
    chat_id = query.message.chat.id
    settings = await get_settings(chat_id)
    req = query.from_user.id
    btn = []
    if settings.get('button'):
        for file in files:
            btn.append([InlineKeyboardButton(
                text=f"{silent_size(file.file_size)}| {extract_tag(file.file_name)} {clean_filename(file.file_name)}",
                callback_data=f'file#{file.file_id}'
            )])
    btn.insert(0, [
        InlineKeyboardButton("qualité", callback_data=f"qualities#{key}#0"),
        InlineKeyboardButton("langue", callback_data=f"languages#{key}#0"),
        InlineKeyboardButton("saison",  callback_data=f"seasons#{key}#0")
    ])
    btn.insert(1, [InlineKeyboardButton("📥 Envoyer tout 📥", callback_data=f"sendfiles#{key}")])
    await build_pagination_buttons(btn, total_results, offset, n_offset, req, key, settings)
    cap = ""
    if not settings.get('button'):
        curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
        time_difference = timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
        remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
        cap = await get_cap(settings, remaining_seconds, files, query, total_results, search_query, offset)
        try:
            await query.message.edit_text(text=cap, reply_markup=InlineKeyboardMarkup(btn), disable_web_page_preview=True, parse_mode=enums.ParseMode.HTML)
        except MessageNotModified:
            pass
    else:
        try:
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(btn))
        except MessageNotModified:
            pass

async def open_category_handler(client, query, items, prefix, title_text):
    try:
        if int(query.from_user.id) not in [query.message.reply_to_message.from_user.id, 0]:
             return await query.answer(
                f"⚠️ Bonjour {query.from_user.first_name},\nce n'est pas votre demande de film,\ndemandez le vôtre...",
                show_alert=True,
            )
    except:
        pass
    _, key, offset = query.data.split("#")
    btn = []
    for i in range(0, len(items)-1, 2):
        btn.append([
            InlineKeyboardButton(
                text=items[i].title(),
                callback_data=f"{prefix}#{items[i].lower()}#{key}#0"
            ),
            InlineKeyboardButton(
                text=items[i+1].title(),
                callback_data=f"{prefix}#{items[i+1].lower()}#{key}#0"
            ),
        ])
    btn.insert(0, [InlineKeyboardButton(text=f"⇊ {title_text} ⇊", callback_data="ident")])
    btn.append([InlineKeyboardButton(text="↭ retour aux fichiers ↭", callback_data=f"{prefix}#homepage#{key}#0")])
    await query.edit_message_reply_markup(InlineKeyboardMarkup(btn))

async def filter_selection_handler(client, query, prefix):
    _, value, key, offset = query.data.split("#")
    if not value:
        await query.answer()
        return
    offset = int(offset)
    if value == "homepage":
        search = FRESH.get(key)
    else:
        search = BUTTONS.get(key) if BUTTONS.get(key) else FRESH.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        return
    search = search.replace("_", " ")
    search = re.sub(r'\s+', ' ', search).strip()
    if value != "homepage":
        category_list = []
        if prefix == "fq":
            category_list = [x for x in QUALITIES if x]
        elif prefix == "fl":
            category_list = [x for x in LANGUAGES if x]
        elif prefix == "fs":
            category_list = [x for x in SEASONS if x]
        is_present = False
        match_pattern = ""
        if prefix == "fs":
            season_search = re.search(r"(?i)season\s*(\d+)", value)
            if season_search:
                season_num = int(season_search.group(1))
                added_regex = f"(s0?{season_num}|season\\s*{season_num})(?:e\\d+)?"
                pattern_combined = re.escape(added_regex)
                if re.search(pattern_combined, search):
                    is_present = True
                    match_pattern = pattern_combined
            else:
                pattern = r'(?i)\b' + re.escape(value) + r'\b'
                if re.search(pattern, search):
                    is_present = True
                    match_pattern = pattern
        elif value.lower().startswith("s") and value[1:].isdigit() and len(value) > 1:
             if value.lower().startswith("s0") and len(value) == 3:
                 short_val = "s" + str(int(value[1:]))
                 added_regex = f"s0?{short_val[1:]}(?:e\\d+)?"
                 pattern_combined = re.escape(added_regex)
                 if re.search(pattern_combined, search):
                     is_present = True
                     match_pattern = pattern_combined
             else:
                pattern = r'(?i)\b' + re.escape(value) + r'\b'
                if re.search(pattern, search):
                    is_present = True
                    match_pattern = pattern
        else:
            pattern = r'(?i)\b' + re.escape(value) + r'\b'
            if re.search(pattern, search):
                is_present = True
                match_pattern = pattern
        if is_present:
            search = re.sub(match_pattern, '', search, count=1)
        else:
            for item in category_list:
                if item.lower() == value.lower():
                    continue
                item_val = item
                if prefix == "fs":
                     season_search = re.search(r"(?i)season\s*(\d+)", item_val)
                     if season_search:
                         season_num = int(season_search.group(1))
                         added_regex = f"(s0?{season_num}|season\\s*{season_num})(?:e\\d+)?"
                         pattern_combined = re.escape(added_regex)
                         search = re.sub(pattern_combined, '', search)
                     elif item_val.lower().startswith("s0") and len(item_val) == 3:
                         short_val = "s" + str(int(item_val[1:]))
                         added_regex = f"s0?{short_val[1:]}(?:e\\d+)?"
                         pattern_combined = re.escape(added_regex)
                         search = re.sub(pattern_combined, '', search)
                     else:
                        pattern = r'(?i)\b' + re.escape(item_val) + r'\b'
                        search = re.sub(pattern, '', search)
                else:
                    pattern = r'(?i)\b' + re.escape(item_val) + r'\b'
                    search = re.sub(pattern, '', search)
            if prefix == "fs":
                 season_search = re.search(r"(?i)season\s*(\d+)", value)
                 if season_search:
                     season_num = int(season_search.group(1))
                     search = f"{search} (s0?{season_num}|season\\s*{season_num})(?:e\\d+)?"
                 else:
                     search = f"{search} {value}"
            elif value.lower().startswith("s") and value[1:].isdigit() and len(value) > 1:
                 if value.lower().startswith("s0") and len(value) == 3:
                     short_val = "s" + str(int(value[1:]))
                     search = f"{search} s0?{short_val[1:]}(?:e\\d+)?"
                 else:
                     search = f"{search} {value}"
            else:
                search = f"{search} {value}"
    search = re.sub(r'\s+', ' ', search).strip()
    BUTTONS[key] = search
    await generic_filter_handler(client, query, key, offset, search)

async def handle_alert_status(client, query, status_text, alert_message, log_hashtag, is_hindi=False):
    ident, from_user = query.data.split("#")
    btn = [[InlineKeyboardButton(status_text, callback_data=f"{ident}alert#{from_user}")]]
    try:
        link = await client.create_chat_invite_link(int(REQST_CHANNEL))
        invite_url = link.invite_link
    except:
        invite_url = GRP_LNK
    btn2 = [[
        InlineKeyboardButton('Rejoindre la chaîne', url=invite_url),
        InlineKeyboardButton("Voir le statut", url=f"{query.message.link}")
    ]]
    if is_hindi or "Available" in status_text or "Uploaded" in status_text:
         btn2.append([InlineKeyboardButton("🔍 Recherchez ici 🔎", url=GRP_LNK)])
    if query.from_user.id in ADMINS:
        user = await client.get_users(from_user)
        reply_markup = InlineKeyboardMarkup(btn)
        content = query.message.text
        await query.message.edit_text(f"<b><strike>{content}</strike></b>")
        await query.message.edit_reply_markup(reply_markup)
        simple_status = status_text.replace("•", "").strip()
        await query.answer(f"Défini sur {simple_status} !")
        content = extract_request_content(query.message.text)
        alert_text = alert_message.format(user_mention=user.mention, content=content)
        try:
            await client.send_message(
                chat_id=int(from_user),
                text=f"{alert_text}\n\n{log_hashtag}",
                reply_markup=InlineKeyboardMarkup(btn2)
            )
        except UserIsBlocked:
             await client.send_message(
                chat_id=int(SUPPORT_CHAT_ID),
                text=f"{alert_text}\n\n{log_hashtag}\n\n<small>Bloqué ? Débloquez le bot pour recevoir des messages.</small>",
                reply_markup=InlineKeyboardMarkup(btn2)
            )
    else:
        await query.answer("Vous n'avez pas les droits suffisants pour faire cela !", show_alert=True)


@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    try:
        ident, req, key, offset = query.data.split("_")
        if int(req) not in [query.from_user.id, 0]:
            return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        try:
            offset = int(offset)
        except:
            offset = 0

        if BUTTONS.get(key)!=None:
            search = BUTTONS.get(key)
        else:
            search = FRESH.get(key)

        if not search:
            await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
            return

        await generic_filter_handler(bot, query, key, offset, search)
        await query.answer()
    except Exception as e:
        LOGGER.error(f"Error In Next Function - {e}")


@Client.on_callback_query(filters.regex(r"^qualities#"))
async def qualities_cb_handler(client: Client, query: CallbackQuery):
    await open_category_handler(client, query, QUALITIES, "fq", "Sélectionner la qualité")

@Client.on_callback_query(filters.regex(r"^fq#"))
async def filter_qualities_cb_handler(client: Client, query: CallbackQuery):
    await filter_selection_handler(client, query, "fq")

@Client.on_callback_query(filters.regex(r"^languages#"))
async def languages_cb_handler(client: Client, query: CallbackQuery):
    await open_category_handler(client, query, LANGUAGES, "fl", "Sélectionner la langue")

@Client.on_callback_query(filters.regex(r"^fl#"))
async def filter_languages_cb_handler(client: Client, query: CallbackQuery):
    await filter_selection_handler(client, query, "fl")
        
@Client.on_callback_query(filters.regex(r"^seasons#"))
async def season_cb_handler(client: Client, query: CallbackQuery):
    await open_category_handler(client, query, SEASONS, "fs", "Sélectionner la saison")

@Client.on_callback_query(filters.regex(r"^fs#"))
async def filter_season_cb_handler(client: Client, query: CallbackQuery):
    await filter_selection_handler(client, query, "fs")

@Client.on_callback_query(filters.regex(r"^spol"))
async def advantage_spoll_choker(bot, query):
    _, id, user = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    movies = await get_poster(id, id=True)
    movie = movies.get('title')
    movie = re.sub(r"[:-]", " ", movie)
    movie = re.sub(r"\s+", " ", movie).strip()
    await query.answer(script.TOP_ALRT_MSG)
    files, offset, total_results = await get_search_results(query.message.chat.id, movie, offset=0, filter=True)
    if files:
        k = (movie, files, offset, total_results)
        await auto_filter(bot, query, k)
    else:
        reqstr1 = query.from_user.id if query.from_user else 0
        reqstr = await bot.get_users(reqstr1)
        if NO_RESULTS_MSG:
            await bot.send_message(chat_id=BIN_CHANNEL,text=script.NORSLTS.format(reqstr.id, reqstr.mention, movie))
        contact_admin_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔰 Cliquez ici et demandez à l'admin🔰", url=OWNER_LNK)]])
        k = await query.message.edit(script.MVE_NT_FND,reply_markup=contact_admin_button)
        await asyncio.sleep(10)
        await k.delete()
                
@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    lazyData = query.data
    try:
        link = await client.create_chat_invite_link(int(REQST_CHANNEL))
    except:
        pass
    if query.data == "close_data":
        await query.message.delete()     
        
    if query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        user = query.message.reply_to_message.from_user.id
        if int(user) != 0 and query.from_user.id != int(user):
            return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
        await query.answer(url=f"https://t.me/{temp.U_NAME}?start=file_{query.message.chat.id}_{file_id}")          
                            
    elif query.data.startswith("sendfiles"):
        clicked = query.from_user.id
        ident, key = query.data.split("#") 
        try:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=allfiles_{query.message.chat.id}_{key}")
            return
        except UserIsBlocked:
            await query.answer('Débloquez le bot !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles3_{key}")
        except Exception as e:
            LOGGER.error(e)
            await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=sendfiles4_{key}")
            
    elif query.data.startswith("del"):
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('Aucun fichier de ce type n\'existe.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                LOGGER.error(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"
        await query.answer(url=f"https://telegram.me/{temp.U_NAME}?start=file_{file_id}")

    elif query.data == "pages":
        await query.answer()    
    
    elif query.data.startswith("killfilesdq"):
        ident, keyword = query.data.split("#")
        await query.message.edit_text(f"<b>Récupération des fichiers pour votre recherche {keyword} dans la base de données... Veuillez patienter...</b>")
        files, total = await get_bad_files(keyword)
        await query.message.edit_text("<b>Le processus de suppression de fichiers débutera dans 5 secondes !</b>")
        await asyncio.sleep(5)
        deleted = 0
        async with lock:
            try:
                for file in files:
                    file_ids = file.file_id
                    file_name = file.file_name
                    result = await Media.collection.delete_one({
                        '_id': file_ids,
                    })
                    if not result.deleted_count and MULTIPLE_DB:
                        result = await Media2.collection.delete_one({
                            '_id': file_ids,
                        })
                    if result.deleted_count:
                        LOGGER.info(f'Fichier trouvé pour votre recherche {keyword}! Supprimé avec succès {file_name} de la base de données.')
                    deleted += 1
                    if deleted % 20 == 0:
                        await query.message.edit_text(f"<b>Processus de suppression des fichiers de la base de données en cours. Supprimé avec succès {str(deleted)} fichiers de la base de données pour votre recherche {keyword} !\n\nVeuillez patienter...</b>")
            except Exception as e:
                LOGGER.error(f"Error In killfiledq -{e}")
                await query.message.edit_text(f'Error: {e}')
            else:
                await query.message.edit_text(f"<b>Processus de suppression de fichiers terminé !\n\nSupprimé avec succès {str(deleted)} fichiers de la base de données pour votre recherche {keyword}.</b>")
    
    elif query.data.startswith("opnsetgrp"):
        ident, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        st = await client.get_chat_member(grp_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            await query.answer("Vous n'avez pas les droits pour faire cela !", show_alert=True)
            return
        title = query.message.chat.title
        btn = await group_setting_buttons(int(grp_id))
        await query.message.edit_text(
                text=f"<b>Modifiez vos paramètres pour {title} comme vous le souhaitez ⚙</b>",
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(btn)
        )
        
    elif query.data.startswith("opnsetpm"):
        ident, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        st = await client.get_chat_member(grp_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            await query.answer("Vous n'avez pas les droits suffisants pour faire cela !", show_alert=True)
            return
        title = query.message.chat.title
        btn2 = [[
                 InlineKeyboardButton("Vérifier mes MP 🗳️", url=f"telegram.me/{temp.U_NAME}")
               ]]
        reply_markup = InlineKeyboardMarkup(btn2)
        await query.message.edit_text(f"<b>Votre menu de paramètres pour {title} a été envoyé en message privé.</b>")
        await query.message.edit_reply_markup(reply_markup)

        btn = await group_setting_buttons(int(grp_id))
        await client.send_message(
            chat_id=userid,
            text=f"<b>Modifiez vos paramètres pour {title} comme vous le souhaitez ⚙</b>",
            reply_markup=InlineKeyboardMarkup(btn),
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML,
            reply_to_message_id=query.message.id
        )

    elif query.data.startswith("show_option"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("• Indisponible •", callback_data=f"unavailable#{from_user}"),
                InlineKeyboardButton("• Téléversé •", callback_data=f"uploaded#{from_user}")
             ],[
                InlineKeyboardButton("• Déjà disponible •", callback_data=f"already_available#{from_user}")
             ],[
                InlineKeyboardButton("• Non sorti •", callback_data=f"Not_Released#{from_user}"),
                InlineKeyboardButton("• Tapez l'orthographe correcte •", callback_data=f"Type_Correct_Spelling#{from_user}")
             ],[
                InlineKeyboardButton("• Non disponible en hindi •", callback_data=f"Not_Available_In_The_Hindi#{from_user}")
             ]]
        if query.from_user.id in ADMINS:
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Voici les options !")
        else:
            await query.answer("Vous n'avez pas les droits suffisants pour faire cela !", show_alert=True)
        
    elif query.data.startswith("unavailable"):
        await handle_alert_status(client, query, "• Indisponible •",
                                  "<b>Salut {user_mention},</b>\n\n<u>{content}</u> A été marqué comme indisponible...💔",
                                  "#Indisponible ⚠️")

    elif query.data.startswith("Not_Released"):
        await handle_alert_status(client, query, "📌 Non sorti 📌",
                                  "<b>Salut {user_mention}\n\n<code>{content}</code>, votre demande n'a pas encore été publiée</b>",
                                  "#Bientôt...🕊️✌️")

    elif query.data.startswith("Type_Correct_Spelling"):
        await handle_alert_status(client, query, "♨️ Tapez l'orthographe correcte ♨️",
                                  "<b>Salut {user_mention}\n\nNous avons refusé votre demande <code>{content}</code>, car votre orthographe était incorrecte 😢</b>",
                                  "#Orthographe_incorrecte 😑")

    elif query.data.startswith("Not_Available_In_The_Hindi"):
        await handle_alert_status(client, query, " Non disponible en hindi ",
                                  "<b>Salut {user_mention}\n\nVotre demande <code>{content}</code> n'est pas disponible en hindi pour le moment. Donc nos modérateurs ne peuvent pas la téléverser</b>",
                                  "#Hindi_non_disponible ❌", is_hindi=True)

    elif query.data.startswith("uploaded"):
        await handle_alert_status(client, query, "• Téléversé •",
                                  "<b>Salut {user_mention},\n\n<u>{content}</u> Votre demande a été téléversée par nos modérateurs.\nVeuillez rechercher dans notre groupe.</b>",
                                  "#Téléversé✅")

    elif query.data.startswith("already_available"):
        await handle_alert_status(client, query, "• Déjà disponible •",
                                  "<b>Salut {user_mention},\n\n<u>{content}</u> Votre demande est déjà disponible dans la base de données de notre bot.\nVeuillez rechercher dans notre groupe.</b>",
                                  "#Disponible 💗")
            
    
    elif query.data.startswith("alalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Salut {user.first_name}, Votre demande est déjà disponible ✅", show_alert=True)
        else:
            await query.answer("Vous n'avez pas les droits suffisants pour faire cela ❌", show_alert=True)

    elif query.data.startswith("upalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Salut {user.first_name}, Votre demande a été téléversée 🔼", show_alert=True)
        else:
            await query.answer("Vous n'avez pas les droits suffisants pour faire cela ❌", show_alert=True)

    elif query.data.startswith("unalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Salut {user.first_name}, Votre demande est indisponible ⚠️", show_alert=True)
        else:
            await query.answer("Vous n'avez pas les droits suffisants pour faire cela ❌", show_alert=True)

    elif query.data.startswith("hnalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Salut {user.first_name}, Ce n'est pas disponible en hindi ❌", show_alert=True)
        else:
            await query.answer("Non autorisé - vous n'êtes pas le demandeur ❌", show_alert=True)

    elif query.data.startswith("nralert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Salut {user.first_name}, Le film/série n'est pas encore sorti 🆕", show_alert=True)
        else:
            await query.answer("Vous ne pouvez pas faire cela car vous n'êtes pas le demandeur original ❌", show_alert=True)

    elif query.data.startswith("wsalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Salut {user.first_name}, Votre demande a été rejetée en raison d'une orthographe incorrecte ❗", show_alert=True)
        else:
            await query.answer("Vous n'avez pas la permission de voir cela ❌", show_alert=True)

    
    elif lazyData.startswith("streamfile"):
        _, file_id = lazyData.split(":")
        try:
            user_id = query.from_user.id
            is_premium_user = await db.has_premium_access(user_id)
            if PAID_STREAM and not is_premium_user:
                premiumbtn = [[InlineKeyboardButton("Acheter Premium ♻️", callback_data='buy')]]
                await query.answer("<b>📌 Cette fonctionnalité est réservée aux utilisateurs premium</b>", show_alert=True)
                await query.message.reply("<b>📌 Cette fonctionnalité est réservée aux utilisateurs premium. Achetez Premium pour y accéder ✅</b>", reply_markup=InlineKeyboardMarkup(premiumbtn))
                return
            username =  query.from_user.mention 
            silent_msg = await client.send_cached_media(
                chat_id=BIN_CHANNEL,
                file_id=file_id,
            )
            fileName = {quote_plus(get_name(silent_msg))}
            silent_stream = f"{URL}watch/{str(silent_msg.id)}/{quote_plus(get_name(silent_msg))}?hash={get_hash(silent_msg)}"
            silent_download = f"{URL}{str(silent_msg.id)}/{quote_plus(get_name(silent_msg))}?hash={get_hash(silent_msg)}"
            btn= [[
                InlineKeyboardButton("Stream", url=silent_stream),
                InlineKeyboardButton("Télécharger", url=silent_download)        
	    ]]
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(btn)
	    )
            await silent_msg.reply_text(
                text=f"•• Lien généré pour l'ID #{user_id} \n•• Nom d'utilisateur : {username} \n\n•• Nom du fichier : {fileName}",
                quote=True,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(btn)
	    )                
        except Exception as e:
            LOGGER.error(e)
            await query.answer(f"⚠️ QUELQUE CHOSE S'EST MAL PASSÉ \n\n{e}", show_alert=True)
            return
           
    
    elif query.data == "pagesn1":
        await query.answer(text=script.PAGE_TXT, show_alert=True)

    elif query.data == "start":
        buttons = [[
                    InlineKeyboardButton('+ Rejoignez Mon Groupe +', url=f'https://t.me/BubleWatchGrp')
                ],[
                    InlineKeyboardButton('🧧 Tendances ', callback_data="topsearch"),
                    InlineKeyboardButton('🎟️ Améliorer ', callback_data="premium"),
                ],[
                    InlineKeyboardButton('♻️ DMCA', callback_data='disclaimer'),
                    InlineKeyboardButton('👤 À propos ', callback_data='me')
                ],[
                    InlineKeyboardButton('🚫 Gagnez de l\'argent avec le bot 🚫', callback_data="earn")
                ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
  
    elif query.data == "give_trial":
        try:
            user_id = query.from_user.id
            has_free_trial = await db.check_trial_status(user_id)
            if has_free_trial:
                await query.answer("🚸 Vous avez déjà réclamé votre essai gratuit une fois !\n\n📌 Vérifiez nos plans via : /plan", show_alert=True)
                return
            else:            
                await db.give_free_trial(user_id)
                await query.message.reply_text(
                    text="<b>🥳 Félicitations\n\n🎉 Vous pouvez utiliser l'essai gratuit pendant <u>5 minutes</u> à partir de maintenant !</b>",
                    quote=False,
                    disable_web_page_preview=True,                  
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💸 Vérifier les plans premium 💸", callback_data='seeplans')]]))
                return    
        except Exception as e:
            LOGGER.error(e)

    elif query.data == "premium":
        try:
            btn = [[
                InlineKeyboardButton('🧧 Acheter premium 🧧', callback_data='buy'),
            ],[
                InlineKeyboardButton('👥 Parrainer des amis', callback_data='reffff'),
                InlineKeyboardButton('🈚 Essai gratuit', callback_data='give_trial')
            ],[            
                InlineKeyboardButton('⇋ Retour à l\'accueil ⇋', callback_data='start')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)                        
            await client.edit_message_media(                
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))                       
            )
            await query.message.edit_text(
                text=script.BPREMIUM_TXT,
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )
        except Exception as e:
            LOGGER.error(e)

    elif query.data == "buy":
        try:
            btn = [[ 
                InlineKeyboardButton('étoiles', callback_data='star'),
                InlineKeyboardButton('upi', callback_data='upi')
            ],[
                InlineKeyboardButton('⋞ Retour', callback_data='premium')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(SUBSCRIPTION)
	        ) 
            await query.message.edit_text(
                text=script.PREMIUM_TEXT.format(query.from_user.mention),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            ) 
        except Exception as e:
            LOGGER.error(e)

    elif query.data == "upi":
        try:
            btn = [[ 
                InlineKeyboardButton('📱 Envoyer une capture d\'écran du paiement', url=OWNER_LNK),
            ],[
                InlineKeyboardButton('⋞ Retour', callback_data='buy')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(SUBSCRIPTION)
	        ) 
            await query.message.edit_text(
                text=script.PREMIUM_UPI_TEXT.format(query.from_user.mention),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            ) 
        except Exception as e:
            LOGGER.error(e)

    elif query.data == "star":
        try:
            btn = [
                InlineKeyboardButton(f"{stars}⭐", callback_data=f"buy_{stars}")
                for stars, days in STAR_PREMIUM_PLANS.items()
            ]
            buttons = [btn[i:i + 2] for i in range(0, len(btn), 2)]
            buttons.append([InlineKeyboardButton("⋞ Retour", callback_data="buy")])
            reply_markup = InlineKeyboardMarkup(buttons)
            await client.edit_message_media(
                query.message.chat.id, 
                query.message.id, 
                InputMediaPhoto(random.choice(PICS))
	        ) 
            await query.message.edit_text(
                text=script.PREMIUM_STAR_TEXT,
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
	    )
        except Exception as e:
            LOGGER.error(e)

    elif query.data == "earn":
        try:
            btn = [[ 
                InlineKeyboardButton('⇋ Retour à l\'accueil ⇋', callback_data='start')
            ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=script.EARN_INFO.format(temp.B_LINK),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            ) 
        except Exception as e:
            LOGGER.error(e)
                    
    elif query.data == "me":
        buttons = [[
            InlineKeyboardButton ('Canal de Films / Series', url='t.me/ZeeXClub'),
        ],[
            InlineKeyboardButton('⇋ Retour à l\'accueil ⇋', callback_data='start')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.U_NAME, temp.B_NAME, OWNER_LNK),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        
    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('Code source 📜', url='https://github.com/NBBotz/Auto-Filter-Bot.git'),
            InlineKeyboardButton('⇋ Retour ⇋', callback_data='me')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "ref_point":
        await query.answer(f'Vous avez: {referdb.get_refer_points(query.from_user.id)} points de parrainage.', show_alert=True)
    
    
    elif query.data == "disclaimer":
            btn = [[
                    InlineKeyboardButton("⇋ Retour ⇋", callback_data="start")
                  ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=(script.DISCLAIMER_TXT),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML 
            )

    elif query.data.startswith("grp_pm"):
        _, grp_id = query.data.split("#")
        user_id = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("Besoin d'être admin pour utiliser cela ✅.", show_alert=True)
        btn = await group_setting_buttons(int(grp_id)) 
        silentx = await client.get_chat(int(grp_id))
        await query.message.edit(text=f"Modifiez vos paramètres de groupe ✅\nNom du groupe - '{silentx.title}'</b>⚙", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("verification_setgs"):
        _, grp_id = query.data.split("#")
        user_id = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>Besoin d'être admin pour utiliser cela ✅.</b>", show_alert=True)

        settings = await get_settings(int(grp_id))
        verify_status = settings.get('is_verify', IS_VERIFY)
        btn = [[
            InlineKeyboardButton(f'vérification: {"activée" if verify_status else "désactivée"}', callback_data=f'toggleverify#is_verify#{verify_status}#{grp_id}'),
	],[
            InlineKeyboardButton('raccourcisseur', callback_data=f'changeshortner#{grp_id}'),
            InlineKeyboardButton('temps', callback_data=f'changetime#{grp_id}')
	],[
            InlineKeyboardButton('tutoriel', callback_data=f'changetutorial#{grp_id}')
        ],[
            InlineKeyboardButton('⇋ Retour ⇋', callback_data=f'grp_pm#{grp_id}')
	]]    
        await query.message.edit("<b>Mode paramètres avancés 📳\n\nVous pouvez personnaliser les valeurs du raccourcisseur et l'intervalle de temps de vérification à partir d'ici ✅\nChoisissez ci-dessous 👇</b>", reply_markup=InlineKeyboardMarkup(btn))
	    

    elif query.data.startswith("log_setgs"):
        _, grp_id = query.data.split("#")
        user_id = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("Besoin d'être admin pour utiliser cela ✅.", show_alert=True)
        btn = [[
            InlineKeyboardButton('canal de logs', callback_data=f'changelog#{grp_id}'),
        ],[
            InlineKeyboardButton('⇋ Retour ⇋', callback_data=f'grp_pm#{grp_id}')
	]]    
        await query.message.edit("<b>Mode paramètres avancés 📳\n\nVous pouvez personnaliser la valeur du canal de logs à partir d'ici ✅\nChoisissez ci-dessous 👇</b>", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("changelog"):
        grp_id = query.data.split("#")[1]
        user_id = query.from_user.id if query.from_user else None
        silentx = await client.get_chat(int(grp_id))
        invite_link = await client.export_chat_invite_link(grp_id)
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>Besoin d'être admin pour utiliser cela ✅.</b>", show_alert=True)
        settings = await get_settings(int(grp_id))
        log_channel = settings.get(f'log', "vous n'avez pas défini de valeur donc utilisation des valeurs par défaut")    
        await query.message.edit(f'<b>📌 Détails du canal de logs.\n\nCanal de logs: <code>{log_channel}</code>.<b>')
        m = await query.message.reply("<b>Envoyez le nouvel ID du canal de logs ( exemple: -100123569303) ou utilisez /cancel pour annuler le processus</b>") 
        while True:
            log_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
            if log_msg.text == "/cancel":
                await m.delete()
                btn = [
                    [InlineKeyboardButton('canal de logs', callback_data=f'changelog#{grp_id}')],
                    [InlineKeyboardButton('⇋ Retour ⇋', callback_data=f'verification_setgs#{grp_id}')]
		]            
                await query.message.edit("<b>Choisissez le canal de logs et modifiez les valeurs comme vous le souhaitez ✅</b>", reply_markup=InlineKeyboardMarkup(btn))
                return        
            if log_msg.text.startswith("-100") and log_msg.text[4:].isdigit() and len(log_msg.text) >= 10:
                try:
                    int(log_msg.text)
                    break 
                except ValueError:
                    await query.message.reply("<b>ID de canal invalide ! Doit être un nombre commençant par -100 (exemple: -100123456789)</b>")
            else:       
                await query.message.reply("<b>ID de canal invalide ! Doit être un nombre commençant par -100 (exemple: -100123456789)</b>")		
        await m.delete()	
        await save_group_settings(int(grp_id), f'log', log_msg.text)
        await client.send_message(LOG_API_CHANNEL, f"#Set_Log_Channel\n\nNom du groupe : {silentx.title}\n\nID du groupe : {grp_id}\nLien d'invitation : {invite_link}\n\nMis à jour par : {query.from_user.username}")	    
        btn = [            
            [InlineKeyboardButton('⇋ Retour ⇋', callback_data=f'verification_setgs#{grp_id}')]
        ]    
        await query.message.reply(f"<b>Canal de logs mis à jour avec succès ✅\nCanal de logs: <code>{log_msg.text}</code></b>", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("caption_setgs"):
        _, grp_id = query.data.split("#")
        user_id = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>Besoin d'être admin pour utiliser cela ✅.</b>", show_alert=True)
        btn = [[
            InlineKeyboardButton('légende personnalisée', callback_data=f'changecaption#{grp_id}'),
        ],[
            InlineKeyboardButton('⇋ Retour ⇋', callback_data=f'grp_pm#{grp_id}')
	]]    
        await query.message.edit("<b>Mode paramètres avancés 📳\n\nVous pouvez personnaliser les valeurs de légende personnalisée à partir d'ici ✅\nChoisissez ci-dessous 👇</b>", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("changecaption"):
        grp_id = query.data.split("#")[1]
        user_id = query.from_user.id if query.from_user else None
        silentx = await client.get_chat(int(grp_id))
        invite_link = await client.export_chat_invite_link(grp_id)
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>Besoin d'être admin pour utiliser cela ✅.</b>", show_alert=True)
        settings = await get_settings(int(grp_id))
        current_caption = settings.get(f'caption', "vous n'avez pas défini de valeur donc utilisation des valeurs par défaut")    
        await query.message.edit(f'<b>📌 Détails de la légende personnalisée.\n\nLégende personnalisée: <code>{current_caption}</code>.</b>')
        m = await query.message.reply("<b>Envoyez la nouvelle légende personnalisée\n\nFormat de légende:\nNom du fichier -<code>{file_name}</code>\nLégende du fichier - <code>{file_caption}</code>\n<code>Taille du fichier - {file_size}</code>\n\nOu utilisez /cancel pour annuler le processus</b>") 
        caption_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
        if caption_msg.text == "/cancel":
            btn = [[
                InlineKeyboardButton('légende personnalisée', callback_data=f'changecaption#{grp_id}'),
	    ],[
                InlineKeyboardButton('⇋ Retour ⇋', callback_data=f'verification_setgs#{grp_id}')]
            ]	
            await query.message.edit("<b>Choisissez la légende personnalisée et modifiez les valeurs comme vous le souhaitez ✅</b>", reply_markup=InlineKeyboardMarkup(btn))
            await m.delete()
            return
        await m.delete()	
        await save_group_settings(int(grp_id), f'caption', caption_msg.text)
        await client.send_message(LOG_API_CHANNEL, f"#Set_Caption\n\nNom du groupe : {title}\n\nID du groupe : {grp_id}\nLien d'invitation : {invite_link}\n\nMis à jour par : {query.from_user.username}")	    
        btn = [            
            [InlineKeyboardButton('⇋ Retour ⇋', callback_data=f'verification_setgs#{grp_id}')]
        ]    
        await query.message.reply(f"<b>Valeurs de légende personnalisée mises à jour avec succès ✅\n\nLégende personnalisée: <code>{caption_msg.text}</code></b>", reply_markup=InlineKeyboardMarkup(btn))

	
    elif query.data.startswith("toggleverify"):
        _, set_type, status, grp_id = query.data.split("#")
        user_id = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>Besoin d'être admin pour utiliser cela ✅.</b>", show_alert=True)    
        new_status = not (status == "True")
        await save_group_settings(int(grp_id), set_type, new_status)
        settings = await get_settings(int(grp_id))
        verify_status = settings.get('is_verify', IS_VERIFY)
        btn = [[
            InlineKeyboardButton(f'vérification: {"activée" if verify_status else "désactivée"}', callback_data=f'toggleverify#is_verify#{verify_status}#{grp_id}'),
	],[
            InlineKeyboardButton('raccourcisseur', callback_data=f'changeshortner#{grp_id}'),
            InlineKeyboardButton('temps', callback_data=f'changetime#{grp_id}')
	],[
            InlineKeyboardButton('tutoriel', callback_data=f'changetutorial#{grp_id}')
        ],[
            InlineKeyboardButton('⇋ Retour ⇋', callback_data=f'grp_pm#{grp_id}')
	]]    
        await query.message.edit("<b>Mode paramètres avancés 📳\n\nVous pouvez personnaliser les valeurs du raccourcisseur et l'intervalle de temps de vérification à partir d'ici ✅\nChoisissez ci-dessous 👇</b>", reply_markup=InlineKeyboardMarkup(btn))


    elif query.data.startswith("changeshortner"):
        _, grp_id = query.data.split("#")
        user_id = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>Besoin d'être admin pour utiliser cela ✅.</b>", show_alert=True)
        btn = [
            [
                InlineKeyboardButton('raccourcisseur 1', callback_data=f'set_verify1#{grp_id}'),
                InlineKeyboardButton('raccourcisseur 2', callback_data=f'set_verify2#{grp_id}')
            ],
            [InlineKeyboardButton('raccourcisseur 3', callback_data=f'set_verify3#{grp_id}')],
            [InlineKeyboardButton('⇋ Retour ⇋', callback_data=f'verification_setgs#{grp_id}')]
		]
        await query.message.edit("<b>Choisissez le raccourcisseur et modifiez les valeurs comme vous le souhaitez ✅</b>", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("set_verify"):
        shortner_num = query.data.split("#")[0][-1]
        grp_id = query.data.split("#")[1]
        user_id = query.from_user.id if query.from_user else None
        silentx = await client.get_chat(int(grp_id))
        invite_link = await client.export_chat_invite_link(grp_id)
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>Besoin d'être admin pour utiliser cela ✅.</b>", show_alert=True)
        settings = await get_settings(int(grp_id))
        suffix = "" if shortner_num == "1" else f"_{'two' if shortner_num == '2' else 'three'}"
        current_url = settings.get(f'shortner{suffix}', "vous n'avez pas défini de valeur donc utilisation des valeurs par défaut")
        current_api = settings.get(f'api{suffix}', "vous n'avez pas défini de valeur donc utilisation des valeurs par défaut")    
        await query.message.edit(f"<b>📌 Détails du raccourcisseur {shortner_num}:\nSite web: <code>{current_url}</code>\nAPI: <code>{current_api}</code></b>")
        m = await query.message.reply("<b>Envoyez le nouveau site web du raccourcisseur ou utilisez /cancel pour annuler le processus</b>") 
        url_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
        if url_msg.text == "/cancel":
            btn = [[
                InlineKeyboardButton('raccourcisseur 1', callback_data=f'set_verify1#{grp_id}'),
                InlineKeyboardButton('raccourcisseur 2', callback_data=f'set_verify2#{grp_id}')
            ],
            [InlineKeyboardButton('raccourcisseur 3', callback_data=f'set_verify3#{grp_id}')],
            [InlineKeyboardButton('⇋ Retour ⇋', callback_data=f'verification_setgs#{grp_id}')]
            ]	
            await query.message.edit("<b>Choisissez le raccourcisseur et modifiez les valeurs comme vous le souhaitez ✅</b>", reply_markup=InlineKeyboardMarkup(btn))
            await m.delete()
            return
        await m.delete()
        n = await query.message.reply("<b>Maintenant envoyez l'API du raccourcisseur ou utilisez /cancel pour annuler le processus</b>")
        key_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
        if key_msg.text == "/cancel":
            btn = [[
                InlineKeyboardButton('raccourcisseur 1', callback_data=f'set_verify1#{grp_id}'),
                InlineKeyboardButton('raccourcisseur 2', callback_data=f'set_verify2#{grp_id}')
            ],
            [InlineKeyboardButton('raccourcisseur 3', callback_data=f'set_verify3#{grp_id}')],
            [InlineKeyboardButton('⇋ Retour ⇋', callback_data=f'verification_setgs#{grp_id}')]
            ]	
            await query.message.edit("<b>Choisissez le raccourcisseur et modifiez les valeurs comme vous le souhaitez ✅</b>", reply_markup=InlineKeyboardMarkup(btn))
            await n.delete()
            return
        await n.delete()    		
        await save_group_settings(int(grp_id), f'shortner{suffix}', url_msg.text)
        await save_group_settings(int(grp_id), f'api{suffix}', key_msg.text)
        log_message = f"#New_Shortner_Set\n\n Numéro du raccourcisseur - {shortner_num}\nLien du groupe - `{invite_link}`\n\nID du groupe : `{grp_id}`\nAjouté par - `{user_id}`\nSite du raccourcisseur - {url_msg.text}\nAPI du raccourcisseur - `{key_msg.text}`"
        await client.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True)
        next_shortner = int(shortner_num) + 1 if shortner_num in ["1", "2"] else None
        btn = [
            [InlineKeyboardButton(f'Raccourcisseur {next_shortner}', callback_data=f'set_verify{next_shortner}#{grp_id}')] if next_shortner else [],
            [InlineKeyboardButton('⇋ Retour ⇋', callback_data=f'verification_setgs#{grp_id}')]
        ]    
        await query.message.reply(f"<b>Valeurs du raccourcisseur {shortner_num} mises à jour avec succès ✅\n\nSite web: <code>{url_msg.text}</code>\nAPI: <code>{key_msg.text}</code></b>", reply_markup=InlineKeyboardMarkup(btn))

    
    elif query.data.startswith("changetime"):
        _, grp_id = query.data.split("#")
        user_id = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>Besoin d'être admin pour utiliser cela ✅.</b>", show_alert=True)
        btn = [
            [
                InlineKeyboardButton('2ème temps de vérification', callback_data=f'set_time2#{grp_id}'),
	    ],[
                InlineKeyboardButton('3ème temps de vérification', callback_data=f'set_time3#{grp_id}')
            ],
            [InlineKeyboardButton('⇋ Retour ⇋', callback_data=f'verification_setgs#{grp_id}')]
		]
        await query.message.edit("<b>Choisissez l'intervalle de temps de vérification et modifiez les valeurs comme vous le souhaitez ✅</b>", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("set_time"):
        time_num = query.data.split("#")[0][-1]
        grp_id = query.data.split("#")[1]
        user_id = query.from_user.id if query.from_user else None
        silentx = await client.get_chat(int(grp_id))
        invite_link = await client.export_chat_invite_link(grp_id)
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>Besoin d'être admin pour utiliser cela ✅.</b>", show_alert=True)
        settings = await get_settings(int(grp_id))
        suffix = "" if time_num == "2" else "third_" if time_num == "3" else ""
        current_time = settings.get(f'{suffix}verify_time', 'Non défini')
        await query.message.edit(f"<b>📌 Détails du {time_num} temps de vérification:\n\nTemps de vérification: {current_time}</b>")
        m = await query.message.reply("<b>Envoyez le nouvel URL du tutoriel ou utilisez /cancel pour annuler le processus.</b>")        
        while True:
            time_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
            if time_msg.text == "/cancel":
                await m.delete()
                btn = [
                    [InlineKeyboardButton('2ème temps de vérification', callback_data=f'set_time2#{grp_id}')],
                    [InlineKeyboardButton('3ème temps de vérification', callback_data=f'set_time3#{grp_id}')],
                    [InlineKeyboardButton('⇋ Retour ⇋', callback_data=f'verification_setgs#{grp_id}')]
		]   
                await query.message.edit("<b>Choisissez le temps de vérification et modifiez les valeurs comme vous le souhaitez ✅</b>", reply_markup=InlineKeyboardMarkup(btn))
                return        
            if time_msg.text.isdigit() and int(time_msg.text) > 0:
                break
            else:
                await query.message.reply("<b>Temps invalide ! Doit être un nombre positif (exemple: 60)</b>")
        await m.delete()
        await save_group_settings(int(grp_id), f'{suffix}verify_time', time_msg.text)
        log_message = f"#New_Time_Set\n\n Numéro du temps - {time_num}\nLien du groupe - `{invite_link}`\n\nID du groupe : `{grp_id}`\nAjouté par - `{user_id}`\nTemps - {time_msg.text}"
        await client.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True)
        next_time = int(time_num) + 1 if time_num in ["2"] else None
        btn = [
            [InlineKeyboardButton(f'{next_time} temps de vérification', callback_data=f'set_time{next_time}#{grp_id}')] if next_time else [],
            [InlineKeyboardButton('⇋ Retour ⇋', callback_data=f'verification_setgs#{grp_id}')]
        ]    
        await query.message.reply(f"<b>{time_num} temps de vérification mis à jour avec succès ✅\n\nTemps de vérification: {time_msg.text}</b>", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("changetutorial"):
        _, grp_id = query.data.split("#")
        user_id = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>Besoin d'être admin pour utiliser cela ✅.</b>", show_alert=True)
        btn = [
            [
                InlineKeyboardButton('tutoriel 1', callback_data=f'set_tutorial1#{grp_id}'),
                InlineKeyboardButton('tutoriel 2', callback_data=f'set_tutorial2#{grp_id}')
            ],
            [InlineKeyboardButton('tutoriel 3', callback_data=f'set_tutorial3#{grp_id}')],
            [InlineKeyboardButton('⇋ Retour ⇋', callback_data=f'verification_setgs#{grp_id}')]
		]
        await query.message.edit("<b>Choisissez le tutoriel et modifiez les valeurs comme vous le souhaitez ✅</b>", reply_markup=InlineKeyboardMarkup(btn))

    elif query.data.startswith("set_tutorial"):
        tutorial_num = query.data.split("#")[0][-1]
        grp_id = query.data.split("#")[1]
        user_id = query.from_user.id if query.from_user else None
        silentx = await client.get_chat(int(grp_id))
        invite_link = await client.export_chat_invite_link(grp_id)
        if not await is_check_admin(client, int(grp_id), user_id):
            return await query.answer("<b>Besoin d'être admin pour utiliser cela ✅.</b>", show_alert=True)
        settings = await get_settings(int(grp_id))
        suffix = "" if tutorial_num == "1" else f"_{'2' if tutorial_num == '2' else '3'}"
        tutorial_url = settings.get(f'tutorial{suffix}', "vous n'avez pas défini de valeur donc utilisation des valeurs par défaut")    
        await query.message.edit(f"<b>📌 Détails du tutoriel {tutorial_num}:\n\nURL du tutoriel: {tutorial_url}.</b>")
        m = await query.message.reply("<b>Envoyez le nouvel URL du tutoriel ou utilisez /cancel pour annuler le processus</b>") 
        tutorial_msg = await client.listen(chat_id=query.message.chat.id, user_id=user_id)
        if tutorial_msg.text == "/cancel":
            btn = [[
                InlineKeyboardButton('tutoriel 1', callback_data=f'set_tutorial1#{grp_id}'),
                InlineKeyboardButton('tutoriel 2', callback_data=f'set_tutorial2#{grp_id}')
            ],
            [InlineKeyboardButton('tutoriel 3', callback_data=f'set_tutorial3#{grp_id}')],
            [InlineKeyboardButton('⇋ Retour ⇋', callback_data=f'verification_setgs#{grp_id}')]
            ]	
            await query.message.edit("<b>Choisissez le tutoriel et modifiez les valeurs comme vous le souhaitez ✅</b>", reply_markup=InlineKeyboardMarkup(btn))
            await m.delete()
            return
        await m.delete()	
        await save_group_settings(int(grp_id), f'tutorial{suffix}', tutorial_msg.text)
        log_message = f"#New_Tutorial_Set\n\n Numéro du tutoriel - {tutorial_num}\nLien du groupe - `{invite_link}`\n\nID du groupe : `{grp_id}`\nAjouté par - `{user_id}`\nTutoriel - {tutorial_msg.text}"
        await client.send_message(LOG_API_CHANNEL, log_message, disable_web_page_preview=True)
        next_tutorial = int(tutorial_num) + 1 if tutorial_num in ["1", "2"] else None
        btn = [
            [InlineKeyboardButton(f'Tutoriel {next_tutorial}', callback_data=f'set_tutorial{next_tutorial}#{grp_id}')] if next_tutorial else [],
            [InlineKeyboardButton('⇋ Retour ⇋', callback_data=f'verification_setgs#{grp_id}')]
        ]    
        await query.message.reply(f"<b>Valeurs du tutoriel {tutorial_num} mises à jour avec succès ✅\n\nURL du tutoriel: {tutorial_msg.text}</b>", reply_markup=InlineKeyboardMarkup(btn))
	    
    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        if not await is_check_admin(client, int(grp_id), userid):
            await query.answer(script.ALRT_TXT, show_alert=True)
            return
			
        if set_type == "auto_del_time":
            new_time = 60 if status == "30" else 120 if status == "60" else AUTO_DELETE_TIME if status == "120" else 30
            await save_group_settings(int(grp_id), "auto_del_time", new_time)
            await query.answer(f"Temps de suppression automatique défini à {new_time}s ✓")
        else:
            if status == "True":
                await save_group_settings(int(grp_id), set_type, False)
                await query.answer("désactivé ✗")
            else:
                await save_group_settings(int(grp_id), set_type, True)
                await query.answer("activé ✓")
				
        btn = await group_setting_buttons(int(grp_id))
        await query.message.edit_reply_markup(InlineKeyboardMarkup(btn))

    await query.answer(MSG_ALRT)

    
async def auto_filter(client, msg, spoll=False):
    curr_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    if not spoll:
        message = msg
        if message.text.startswith("/"): return
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if len(message.text) < 100:
            search = await replace_words(message.text)		
            search = search.lower()
            search = search.replace("-", " ")
            search = search.replace(":","")
            search = re.sub(r'\s+', ' ', search).strip()
            m=await message.reply_text(f'<b>Attendez {message.from_user.mention} Recherche de votre requête: <i>{search}...</i></b>', reply_to_message_id=message.id)
            files, offset, total_results = await get_search_results(message.chat.id ,search, offset=0, filter=True)
            settings = await get_settings(message.chat.id)
            if not files:
                if settings["spell_check"]:
                    ai_sts = await m.edit('🤖 Veuillez patienter, l\'IA vérifie votre orthographe...')
                    is_misspelled = await ai_spell_check(chat_id = message.chat.id,wrong_name=search)
                    if is_misspelled:
                        await ai_sts.edit(f'<b>✅ L\'IA a suggéré <code> {is_misspelled}</code> \nDonc je recherche pour <code>{is_misspelled}</code></b>')
                        await asyncio.sleep(2)
                        message.text = is_misspelled
                        await ai_sts.delete()
                        return await auto_filter(client, message)
                    await ai_sts.delete()
                    return await advantage_spell_chok(client, message)
        else:
            return
    else:
        message = msg.message.reply_to_message
        search, files, offset, total_results = spoll
        m=await message.reply_text(f'<b>Attendez {message.from_user.mention} Recherche de votre requête:<i>{search}...</i></b>', reply_to_message_id=message.id)
        settings = await get_settings(message.chat.id)
        await msg.message.delete()
    
    key = f"{message.chat.id}-{message.id}"
    FRESH[key] = search
    temp.GETALL[key] = files
    temp.SHORT[message.from_user.id] = message.chat.id
    btn = []
    
    if settings.get('button'):
        for file in files:
            btn.append([InlineKeyboardButton(
                text=f"{silent_size(file.file_size)}| {extract_tag(file.file_name)} {clean_filename(file.file_name)}",
                callback_data=f'file#{file.file_id}'
            )])
    
    btn.insert(0, [
        InlineKeyboardButton("qualité", callback_data=f"qualities#{key}#0"),
        InlineKeyboardButton("langue", callback_data=f"languages#{key}#0"),
        InlineKeyboardButton("saison",  callback_data=f"seasons#{key}#0")
    ])
    btn.insert(1, [InlineKeyboardButton("📥 Envoyer tout 📥", callback_data=f"sendfiles#{key}")])

    if offset != "":
        req = message.from_user.id if message.from_user else 0
        await build_pagination_buttons(btn, total_results, 0, offset, req, key, settings)
    else:
        btn.append([InlineKeyboardButton(text="↭ aucune autre page disponible ↭",callback_data="pages")])
    
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    cur_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
    time_difference = timedelta(hours=cur_time.hour, minutes=cur_time.minute, seconds=(cur_time.second+(cur_time.microsecond/1000000))) - timedelta(hours=curr_time.hour, minutes=curr_time.minute, seconds=(curr_time.second+(curr_time.microsecond/1000000)))
    remaining_seconds = "{:.2f}".format(time_difference.total_seconds())
    DELETE_TIME = settings.get("auto_del_time", AUTO_DELETE_TIME)
    TEMPLATE = script.IMDB_TEMPLATE_TXT    
    poster_url = None
    if imdb:
        if IS_LANDSCAPE_POSTER:
            tmdb_data = await fetch_tmdb_data(search, imdb.get('year'))
            if tmdb_data:
                backdrop_url = await get_best_visual(tmdb_data)
                if backdrop_url:
                    poster_url = backdrop_url        
            if not poster_url:
                poster_url = imdb.get('poster')  
        else:
            poster_url = imdb.get('poster')
    if imdb:
        cap = TEMPLATE.format(
            qurey=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
        temp.IMDB_CAP[message.from_user.id] = cap
        if not settings.get('button'):
            for file_num, file in enumerate(files, start=1):
                cap += f"\n\n<b>{file_num}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}'>{get_size(file.file_size)} | {clean_filename(file.file_name)}</a></b>"
    else:
        if settings.get('button'):
            cap = f"<b><blockquote>Salut,{message.from_user.mention}</blockquote>\n\n📂 Voici ce que j'ai trouvé pour votre recherche <code>{search}</code></b>\n\n"
        else:
            cap = f"<b><blockquote>Salut,{message.from_user.mention}</blockquote>\n\n📂 Voici ce que j'ai trouvé pour votre recherche <code>{search}</code></b>\n\n"            
            for file_num, file in enumerate(files, start=1):
                cap += f"<b>{file_num}. <a href='https://telegram.me/{temp.U_NAME}?start=file_{message.chat.id}_{file.file_id}'>{get_size(file.file_size)} | {clean_filename(file.file_name)}\n\n</a></b>"                  
    try:
        if imdb and poster_url:
            try:
                hehe = await message.reply_photo(
                    photo=poster_url,
                    caption=cap, 
                    reply_markup=InlineKeyboardMarkup(btn), 
                    parse_mode=enums.ParseMode.HTML
                )
                await m.delete()
                if settings['auto_delete']:
                    await asyncio.sleep(DELETE_TIME)
                    await hehe.delete()
                    await message.delete()
            except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
                pic = imdb.get('poster')
                if pic:
                    poster = pic.replace('.jpg', "._V1_UX360.jpg")
                    hmm = await message.reply_photo(
                        photo=poster, 
                        caption=cap, 
                        reply_markup=InlineKeyboardMarkup(btn), 
                        parse_mode=enums.ParseMode.HTML
                    )
                    await m.delete()
                    if settings['auto_delete']:
                        await asyncio.sleep(DELETE_TIME)
                        await hmm.delete()
                        await message.delete()
                else:
                    fek = await m.edit_text(
                        text=cap, 
                        reply_markup=InlineKeyboardMarkup(btn), 
                        parse_mode=enums.ParseMode.HTML
                    )
                    if settings['auto_delete']:
                        await asyncio.sleep(DELETE_TIME)
                        await fek.delete()
                        await message.delete()
            except Exception as e:
                LOGGER.error(e)
                fek = await m.edit_text(
                    text=cap, 
                    reply_markup=InlineKeyboardMarkup(btn), 
                    parse_mode=enums.ParseMode.HTML
                )
                if settings['auto_delete']:
                    await asyncio.sleep(DELETE_TIME)
                    await fek.delete()
                    await message.delete()
        else:
            fuk = await m.edit_text(
                text=cap, 
                reply_markup=InlineKeyboardMarkup(btn), 
                disable_web_page_preview=True, 
                parse_mode=enums.ParseMode.HTML
            )
            if settings['auto_delete']:
                await asyncio.sleep(DELETE_TIME)
                await fuk.delete()
                await message.delete()
    except KeyError:
        await save_group_settings(message.chat.id, 'auto_delete', True)
        pass

async def ai_spell_check(chat_id, wrong_name):
    async def search_movie(wrong_name):
        search_results = await asyncio.to_thread(imdb.search_movie, wrong_name)
        movie_list = [movie['title'] for movie in search_results]
        return movie_list
    movie_list = await search_movie(wrong_name)
    if not movie_list:
        return
    for _ in range(5):
        closest_match = process.extractOne(wrong_name, movie_list)
        if not closest_match or closest_match[1] <= 80:
            return 
        movie = closest_match[0]
        files, offset, total_results = await get_search_results(chat_id=chat_id, query=movie)
        if files:
            return movie
        movie_list.remove(movie)

async def advantage_spell_chok(client, message):
    mv_id = message.id
    search = message.text
    chat_id = message.chat.id
    settings = await get_settings(chat_id)
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", message.text, flags=re.IGNORECASE)
    query = query.strip() + " movie"
    try:
        movies = await get_poster(search, bulk=True)
    except:
        k = await message.reply(script.I_CUDNT.format(message.from_user.mention))
        await asyncio.sleep(60)
        await k.delete()
        try:
            await message.delete()
        except:
            pass
        return
    if not movies:
        google = search.replace(" ", "+")
        button = [[
            InlineKeyboardButton("🔍 Vérifiez l'orthographe sur Google 🔍", url=f"https://www.google.com/search?q={google}")
        ]]
        k = await message.reply_text(text=script.I_CUDNT.format(search), reply_markup=InlineKeyboardMarkup(button))
        await asyncio.sleep(60)
        await k.delete()
        try:
            await message.delete()
        except:
            pass
        return
    user = message.from_user.id if message.from_user else 0
    buttons = [[
        InlineKeyboardButton(text=movie.get('title'), callback_data=f"spol#{movie.movieID}#{user}")
    ]
        for movie in movies
    ]
    buttons.append(
        [InlineKeyboardButton(text="🚫 Fermer 🚫", callback_data='close_data')]
    )
    d = await message.reply_text(text=script.CUDNT_FND.format(message.from_user.mention), reply_markup=InlineKeyboardMarkup(buttons), reply_to_message_id=message.id)
    await asyncio.sleep(60)
    await d.delete()
    try:
        await message.delete()
    except:
        pass