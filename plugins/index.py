import time
import re
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, ChatAdminRequired, UsernameInvalid, UsernameNotModified
from info import ADMINS, INDEX_REQ_CHANNEL as LOG_CHANNEL
from database.ia_filterdb import save_file
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import temp, get_readable_time
from math import ceil
from logging_helper import LOGGER


lock = asyncio.Lock()

@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    if query.data.startswith('index_cancel'):
        temp.CANCEL = True
        return await query.answer("Annulation de l'indexation")
    _, raju, chat, lst_msg_id, from_user = query.data.split("#")
    if raju == 'reject':
        await query.message.delete()
        await bot.send_message(int(from_user),
                               f'Votre soumission pour indexer {chat} a été refusée par nos modérateurs.',
                               reply_to_message_id=int(lst_msg_id))
        return

    if lock.locked():
        return await query.answer('Attendez que le processus précédent soit terminé.', show_alert=True)
    msg = query.message

    await query.answer('Traitement en cours...⏳', show_alert=True)
    if int(from_user) not in ADMINS:
        await bot.send_message(int(from_user),
                               f'Votre soumission pour indexer {chat} a été acceptée par nos modérateurs et sera ajoutée bientôt.',
                               reply_to_message_id=int(lst_msg_id))
    await msg.edit(
        "Début de l'indexation",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('Annuler', callback_data='index_cancel')]]
        )
    )
    try:
        chat = int(chat)
    except:
        chat = chat
    await index_files_to_db(int(lst_msg_id), chat, msg, bot)


@Client.on_message((filters.forwarded | (filters.regex(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")) & filters.text ) & filters.private & filters.incoming)
async def send_for_index(bot, message):
    if message.text:
        regex = re.compile(r"(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(message.text)
        if not match:
            return await message.reply('Lien invalide')
        chat_id = match.group(4)
        last_msg_id = int(match.group(5))
        if chat_id.isnumeric():
            chat_id  = int(("-100" + chat_id))
    elif message.forward_from_chat and message.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = message.forward_from_message_id
        chat_id = message.forward_from_chat.username or message.forward_from_chat.id
    else:
        return
    try:
        await bot.get_chat(chat_id)
    except ChannelInvalid:
        return await message.reply('Ceci peut être un canal/groupe privé. Faites-moi administrateur là-bas pour indexer les fichiers.')
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('Lien spécifié invalide.')
    except Exception as e:
        LOGGER.error(e)
        return await message.reply(f'Erreurs - {e}')
    try:
        k = await bot.get_messages(chat_id, last_msg_id)
    except:
        return await message.reply('Assurez-vous que je suis administrateur dans le canal, si le canal est privé')
    if k.empty:
        return await message.reply('Ceci peut être un groupe et je ne suis pas administrateur du groupe.')

    if message.from_user.id in ADMINS:
        buttons = [
            [InlineKeyboardButton('Oui', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')],
            [InlineKeyboardButton('Fermer', callback_data='close_data')]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        return await message.reply(
            f'Voulez-vous indexer ce canal/groupe ?\n\nID/Nom du chat : <code>{chat_id}</code>\nDernier ID de message : <code>{last_msg_id}</code>\n\nBesoin de définir skip 👉🏻 /setskip',
            reply_markup=reply_markup)

    if type(chat_id) is int:
        try:
            link = (await bot.create_chat_invite_link(chat_id)).invite_link
        except ChatAdminRequired:
            return await message.reply('Assurez-vous que je suis administrateur du chat et que j\'ai la permission d\'inviter des utilisateurs.')
    else:
        link = f"@{message.forward_from_chat.username}"
    buttons = [
        [InlineKeyboardButton('Accepter l\'indexation', callback_data=f'index#accept#{chat_id}#{last_msg_id}#{message.from_user.id}')],
        [InlineKeyboardButton('Refuser l\'indexation', callback_data=f'index#reject#{chat_id}#{message.id}#{message.from_user.id}')]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await bot.send_message(LOG_CHANNEL,
                           f'#DemandeIndexation\n\nPar : {message.from_user.mention} (<code>{message.from_user.id}</code>)\nID/Nom du chat - <code> {chat_id}</code>\nDernier ID de message - <code>{last_msg_id}</code>\nLien d\'invitation - {link}',
                           reply_markup=reply_markup)
    await message.reply('Merci pour votre contribution, attendez que nos modérateurs vérifient les fichiers.')


@Client.on_message(filters.command('setskip') & filters.user(ADMINS))
async def set_skip_number(bot, message):
    if ' ' in message.text:
        _, skip = message.text.split(" ")
        try:
            skip = int(skip)
        except:
            return await message.reply("Le nombre de skip doit être un entier.")
        await message.reply(f"Nombre SKIP défini avec succès sur {skip}")
        temp.CURRENT = int(skip)
    else:
        await message.reply("Donnez-moi un nombre de skip")

def get_progress_bar(percent, length=10):
    filled = int(length * percent / 100)
    unfilled = length - filled
    return '█' * filled + '▒' * unfilled

async def index_files_to_db(lst_msg_id, chat, msg, bot):
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    unsupported = 0
    BATCH_SIZE = 200
    start_time = time.time()

    async with lock:
        try:
            current = temp.CURRENT
            temp.CANCEL = False
            total_messages = lst_msg_id
            total_fetch = lst_msg_id - current
            if total_messages <= 0:
                await msg.edit(
                    "🚫 Aucun message à indexer.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Fermer', callback_data='close_data')]])
                )
                return
            batches = ceil(total_messages / BATCH_SIZE)
            batch_times = []
            await msg.edit(
                f"📊 Début de l'indexation......\n"
                f"💬 Messages totaux : <code>{total_messages}</code>\n"
                f"💾 Total à récupérer : <code> {total_fetch}</code>\n"
                f"⏰ Écoulé : <code>{get_readable_time(time.time() - start_time)}</code>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Annuler', callback_data='index_cancel')]])
            )
            for batch in range(batches):
                if temp.CANCEL:
                    break
                batch_start = time.time()
                start_id = current + 1
                end_id = min(current + BATCH_SIZE, lst_msg_id)
                message_ids = range(start_id, end_id + 1)
                try:
                    messages = await bot.get_messages(chat, list(message_ids))
                    if not isinstance(messages, list):
                        messages = [messages]
                except Exception as e:
                    errors += len(message_ids)
                    current += len(message_ids)
                    continue
                save_tasks = []
                for message in messages:
                    current += 1
                    try:
                        if message.empty:
                            deleted += 1
                            continue
                        elif not message.media:
                            no_media += 1
                            continue
                        elif message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT]:
                            unsupported += 1
                            continue
                        media = getattr(message, message.media.value, None)
                        if not media:
                            unsupported += 1
                            continue
                        media.file_type = message.media.value
                        media.caption = message.caption
                        save_tasks.append(save_file(media))

                    except Exception:
                        errors += 1
                        continue
                results = await asyncio.gather(*save_tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        errors += 1
                    else:
                        ok, code = result
                        if ok:
                            total_files += 1
                        elif code == 0:
                            duplicate += 1
                        elif code == 2:
                            errors += 1
                batch_time = time.time() - batch_start
                batch_times.append(batch_time)
                elapsed = time.time() - start_time
                progress = current - temp.CURRENT
                percentage = (progress / total_fetch) * 100
                avg_batch_time = sum(batch_times) / len(batch_times) if batch_times else 1
                eta = (total_fetch - progress) / BATCH_SIZE * avg_batch_time
                progress_bar = get_progress_bar(int(percentage))
                await msg.edit(
                    f"📊 Progression de l'indexation\n"
                    f"📦 Lot n° : {batch + 1}/{batches}\n"
                    f"{progress_bar} <code>{percentage:.1f}%</code>\n"
                    f"💬 Messages totaux : <code>{total_messages}</code>\n"
                    f"📥 Total à récupérer : <code>{total_fetch}</code>\n"
                    f"⬇️ Récupérés : <code>{current}</code>\n"
                    f"💾 Sauvegardés : <code>{total_files}</code>\n"
                    f"🔄 Doublons : <code>{duplicate}</code>\n"
                    f"🗑️ Supprimés : <code>{deleted}</code>\n"
                    f"📴 Non-médias : <code>{no_media + unsupported}</code> (🚫 Non supportés : <code>{unsupported}</code>)\n"
                    f"⚠️ Erreurs : <code>{errors}</code>\n"
                    f"⏱️ Écoulé : <code>{get_readable_time(elapsed)}</code>\n"
                    f"⏰ ETA : <code>{get_readable_time(eta)}</code>",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Annuler', callback_data='index_cancel')]])
                )
            elapsed = time.time() - start_time
            await msg.edit(
                f"✅ Indexation terminée !\n"
                f"💬 Messages totaux : <code>{total_messages}</code>\n" 
                f"📥 Total à récupérer : <code>{total_fetch}</code>\n"
                f"⬇️ Récupérés : <code>{current}</code>\n"
                f"💾 Sauvegardés : <code>{total_files}</code>\n"
                f"🔄 Doublons : <code>{duplicate}</code>\n"
                f"🗑️ Supprimés : <code>{deleted}</code>\n"
                f"📴 Non-médias : <code>{no_media + unsupported}</code> (Non supportés : <code>{unsupported}</code>)\n"
                f"⚠️ Erreurs : <code>{errors}</code>\n"
                f"⏰ Écoulé : <code>{get_readable_time(elapsed)}</code>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Fermer', callback_data='close_data')]])
            )
        except Exception as e:
            await msg.edit(
                f"❌ Erreur : <code>{e}</code>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Fermer', callback_data='close_data')]])
            )