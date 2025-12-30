class script(object):
    START_TXT = """<b>👋 Bonjour {},

Je suis un bot de filtrage automatique avancé.

Je peux fournir des films, séries, animes, et bien plus encore... 🎬

Il suffit de m'envoyer le nom du film/série que vous voulez. 🔍</b>"""

    FEATURES_TXT = """<b>🛠️ Voici mes fonctionnalités disponibles 🛠️</b>"""

    ABOUT_TXT = """<b>╭───────────⍟
├🤖 Mon nom : <a href=https://t.me/{}>{}</a>
├👑 Propriétaire : <a href={}>Propriétaire</a>
├👨‍💻 Développeur : <a href=https://t.me/WorldZPrime>ZeeXClub</a>
├📕 Bibliothèque : <a href=https://pyrogram.org>Pyrogram</a>
├✏️ Langage : <a href=https://www.python.org>Python 3</a>
├💾 Base de données : MySQL
├📊 Version : V4.3 [ Stable ]
╰───────────────⍟</b>"""

    FORCESUB_TEXT = """<b>⚠️ Accès refusé ⚠️

Vous devez rejoindre notre chaîne de mise à jour pour accéder à ce bot.

👇 Étapes de vérification :
1️⃣ Cliquez sur le bouton "Rejoindre la chaîne de mise à jour".
2️⃣ Rejoignez la chaîne.
3️⃣ Cliquez sur le bouton "Réessayer".

✨ Merci pour votre soutien !</b>"""
           
    MULTI_STATUS_TXT = """<b>╭─[ ⚡ État de la base de données ⚡ ]─⍟</b>
│
<b>├─[ Base de données 1 ]─⍟</b>
├⋟ 👤 Utilisateurs ⋟ <code>{}</code>
├⋟ 👥 Groupes ⋟ <code>{}</code>
├⋟ 💎 Premium ⋟ <code>{}</code>
├⋟ 📂 Fichiers ⋟ <code>{}</code>
├⋟ 💾 Utilisé ⋟ <code>{}</code>
├⋟ 🆓 Libre ⋟ <code>{}</code>
│
<b>├─[ Base de données 2 ]─⍟</b>
├⋟ 📂 Fichiers ⋟ <code>{}</code>
├⋟ 💾 Taille ⋟ <code>{}</code>
├⋟ 🆓 Libre ⋟ <code>{}</code>
│
<b>├─[ 🤖 Détails du bot ]─⍟</b>
├⋟ ⏳ Temps de fonctionnement ⋟ {}
├⋟ ⚡ RAM ⋟ <code>{}%</code>
├⋟ 🔋 CPU ⋟ <code>{}%</code>
│
├⋟ 📊 Total des fichiers : <code>{}</code>
<b>╰──────────────────────⍟</b>"""

    STATUS_TXT = """<b>╭─[ ⚡ État de la base de données ⚡ ]─⍟</b>
│
<b>├─[ Base de données ]─⍟</b>
├⋟ 👤 Utilisateurs ⋟ <code>{}</code>
├⋟ 👥 Groupes ⋟ <code>{}</code>
├⋟ 💎 Premium ⋟ <code>{}</code>
├⋟ 📂 Fichiers ⋟ <code>{}</code>
├⋟ 💾 Utilisé ⋟ <code>{}</code>
├⋟ 🆓 Libre ⋟ <code>{}</code>
│
<b>├─[ 🤖 Détails du bot ]─⍟</b>
├⋟ ⏳ Temps de fonctionnement ⋟ {}
├⋟ ⚡ RAM ⋟ <code>{}%</code>
├⋟ 🔋 CPU ⋟ <code>{}%</code>
<b>╰──────────────────────⍟</b>"""

    EARN_INFO = """<b>💰 <u>Comment gagner de l'argent avec ce bot</u> 💰

1️⃣ Vous devez avoir un groupe avec au moins 100 membres.
2️⃣ Ajoutez <a href=https://t.me/{}>ce bot</a> en tant qu'administrateur dans votre groupe.
3️⃣ Créez un compte sur un service de raccourcissement d'URL (ex. <a href=https://zipshort.net/>Zipshort</a>).
4️⃣ Envoyez /settings dans votre groupe et configurez le raccourcisseur.

🔍 Voir les détails : /details

💡 Note : Ce bot est gratuit et vous aide à monétiser votre groupe !</b>"""


    VERIFICATION_TEXT = """<b>👋 Salut {},

🔒 Vérification requise !

Vous n'êtes pas vérifié. Veuillez vérifier pour obtenir un accès illimité.

📊 État de vérification : 1/3

💡 <i>Vous voulez éviter cela ? Achetez Premium pour les fichiers directs !</i></b>"""
    

    VERIFY_COMPLETE_TEXT = """<b>🎉 Félicitations {},

✅ Vérification 1/3 terminée !

Vous avez maintenant accès jusqu'au prochain point de contrôle.</b>"""

    SECOND_VERIFICATION_TEXT = """<b>👋 Salut {},

🔒 Vérification requise !

Vous n'êtes pas vérifié. Veuillez vérifier pour obtenir un accès illimité.

📊 État de vérification : 2/3

💡 <i>Vous voulez éviter cela ? Achetez Premium pour les fichiers directs !</i></b>"""

    SECOND_VERIFY_COMPLETE_TEXT = """<b>🎉 Félicitations {},

✅ Vérification 2/3 terminée !

Vous avez maintenant accès jusqu'au prochain point de contrôle.</b>"""

    THIRDT_VERIFICATION_TEXT = """<b>👋 Salut {},

🔒 Vérification requise !

Vous n'êtes pas vérifié. Veuillez vérifier pour obtenir un accès illimité pendant 24 heures.

📊 État de vérification : 3/3

💡 <i>Vous voulez éviter cela ? Achetez Premium pour les fichiers directs !</i></b>"""

    THIRDT_VERIFY_COMPLETE_TEXT= """<b>🎉 Félicitations {},

✅ Vérification 3/3 terminée !

Vous avez maintenant un accès illimité pour les 24 prochaines heures.</b>"""

    VERIFIED_LOG_TEXT = """<b>#VérificationTerminée

👤 Utilisateur : {} [ <code>{}</code> ]
📆 Date : <code>{}</code>
📊 Statut : #Vérification_{}_Terminée</b>"""
       
    LOG_TEXT_G = """<b>#NouveauGroupe

🏠 Groupe : {}
🆔 ID : <code>{}</code>
👥 Membres : <code>{}</code>
👤 Ajouté par : {}</b>"""

    LOG_TEXT_P = """<b>#NouvelUtilisateur

🆔 ID : <code>{}</code>
👤 Nom : {}</b>"""

    ALRT_TXT = """Bonjour {},
ce n'est pas votre demande de film,
demandez le vôtre..."""

    OLD_ALRT_TXT = """Hé {},
vous utilisez un de mes anciens messages,
veuillez renvoyer la demande."""

    CUDNT_FND = """Je n'ai rien trouvé concernant {}
Vouliez-vous dire l'un de ceux-ci ?"""

    I_CUDNT = """<b><i>Ce film n'est actuellement pas disponible.

Il n'a pas encore été publié ou n'a pas encore été ajouté à la base de données.</i></b>"""
    
    I_CUD_NT = """<b><i>Ce film n'est actuellement pas disponible.

Il n'a pas encore été publié ou n'a pas encore été ajouté à la base de données.</i></b>"""
    
    MVE_NT_FND = """<b><i>Ce film n'est actuellement pas disponible.

Il n'a pas encore été publié ou n'a pas encore été ajouté à la base de données.</i></b>"""
    
    TOP_ALRT_MSG = """Recherche de requête dans ma base de données..."""

    MELCOW_ENG = """<b>👋 Bonjour {},\n\n🍁 Bienvenue dans\n🌟 {}\n\n🔍 Tapez simplement le nom du film ou de la série que vous voulez télécharger.\n\n⚠️ Besoin d'aide ? Contactez-nous ici 👇</b>"""
    
    DISCLAIMER_TXT = """
<b>Il s'agit d'un projet open source.

Tous les fichiers de ce bot sont librement disponibles sur Internet ou publiés par quelqu'un d'autre. Ce bot indexe simplement les fichiers déjà téléchargés sur Telegram pour faciliter la recherche. Nous respectons toutes les lois sur le droit d'auteur et travaillons en conformité avec le DMCA et l'EUCD. Si quelque chose est illégal, veuillez me contacter pour qu'il puisse être supprimé dès que possible. Il est interdit de télécharger, diffuser, reproduire, partager ou consommer du contenu sans l'autorisation explicite du créateur ou du détenteur des droits d'auteur. Si vous pensez que ce bot viole votre propriété intellectuelle, contactez les chaînes respectives pour suppression. Le bot ne possède aucun de ces contenus, il indexe uniquement les fichiers de Telegram.
</b>"""

    PREMIUM_TEXT = """<b>💎 <u>Forfaits Premium</u> 💎

🗓️ 07 jours  ➪  500 XOf / 15 ⭐
🗓️ 15 jours  ➪  1000 XOf / 30 ⭐
🗓️ 01 mois ➪  2000 XOf / 60 ⭐
🗓️ 02 mois ➪  3500 XOf / 120 ⭐
🗓️ 03 mois ➪  6000 XOf / 220 ⭐

<b>NB: les paiements sont aussi faisable en Franc Congolais, EUR, USD et Crypto


⚠️ Important :
1️⃣ Envoyez une capture d'écran après paiement.
2️⃣ Attendez la confirmation de l'administrateur pour être ajouté.</b>"""

    PREMIUM_STAR_TEXT = """<b><blockquote>Méthode de paiement : Étoiles Telegram ⭐</blockquote>

Vous pouvez maintenant acheter notre service premium en utilisant les étoiles Telegram.  

Si vous rencontrez un problème, prenez une capture d'écran et envoyez-la à - @WorldZPrimeBot

Sélectionnez le montant désiré et achetez un abonnement 👇.</b>
"""

    PREMIUM_UPI_TEXT = """<b><blockquote>Méthode de paiement : Mobile money, Crypto </blockquote>

Vous pouvez acheter Premium via Mobile Money.

💳 Virement bancaire - <code>non disponible actuellement</code>

💢 Doit envoyer une capture d'écran après paiement.

‼️ Après avoir envoyé la capture d'écran, veuillez nous laisser un peu de temps pour vous ajouter à la liste Premium.</b>"""
    
    
    BPREMIUM_TXT = """<blockquote>🎁 <b>Fonctionnalités Premium</b> :</blockquote>

○ Pas besoin de vérification
○ Pas besoin d'ouvrir les liens
○ Fichiers directs   
○ Expérience sans publicité 
○ Liens de téléchargement haute vitesse                         
○ Liens de streaming multi-joueurs                           
○ Films et séries illimités                                                                        
○ Support administrateur complet                              
○ Les demandes seront complétées en 1h [ si disponible ]

• Vous pouvez obtenir Premium en parrainant vos amis ou vous pouvez acheter le service premium 

•─────•─────────•─────•
◉ Vérifiez votre plan actif : /myplan

‼️ Après avoir envoyé la capture d'écran, laissez-nous un peu de temps pour vous ajouter à la liste Premium."""   
    
      
    NORSLTS = """ 
#AucunRésultat

ID : <code>{}</code>
Nom : {}

Message : <b>{}</b>"""
    
    CAPTION = """<b>{file_name}\n
📤 Téléversé par : <a href="https://t.me/BubleWatch">Buble Watch</a></b>"""

    IMDB_TEMPLATE_TXT = """
<b>🎬 Titre : <a href={url}>{title}</a>
🎭 Genres : {genres}
📅 Année : <a href={url}/releaseinfo>{year}</a>
⭐ Note : <a href={url}/ratings>{rating}</a> / 10 ({votes} votes)
💿 Durée : {runtime} minutes

⏳ Résultats affichés en : {remaining_seconds} secondes
👤 Demandé par : {message.from_user.mention}</b>"""

    RESTART_TXT = """
<b>✅ Bot redémarré !

📅 Date : <code>{}</code>
⏰ Heure : <code>{}</code>
🌐 Fuseau horaire : <code>Asie/Kolkata</code>
🛠️ Version : <code>v4.3 [ Stable ]</code>
</b>"""
    LOGO = """
  ____  _ _            _  __  ______        _       
 / ___|(_) | ___ _ __ | |_\ \/ / __ )  ___ | |_ ____
 \___ \| | |/ _ \ '_ \| __|\  /|  _ \ / _ \| __|_  /
  ___) | | |  __/ | | | |_ /  \| |_) | (_) | |_ / / 
 |____/|_|_|\___|_| |_|\__/_/\_\____/ \___/ \__/___|
                                                                                                                                                                            
BOT FONCTIONNANT CORRECTEMENT...."""

    ADMIN_CMD = """<b>👮‍♂️ Commandes administrateur :

• /movie_update - <code>activer/désactiver les mises à jour de films</code>
• /pm_search - <code>activer/désactiver la recherche en MP</code>
• /verifyon - <code>activer la vérification</code>
• /verifyoff - <code>désactiver la vérification</code>
• /logs - <code>vérifier les logs d'erreur</code>
• /delete - <code>supprimer un fichier de la base de données</code>
• /users - <code>liste des utilisateurs</code>
• /chats - <code>liste des groupes</code>
• /leave  - <code>quitter un groupe</code>
• /disable  - <code>désactiver un groupe</code>
• /ban  - <code>bannir un utilisateur</code>
• /unban  - <code>débannir un utilisateur</code>
• /channel - <code>liste des groupes connectés</code>
• /broadcast - <code>diffuser aux utilisateurs</code>
• /grp_broadcast - <code>diffuser aux groupes</code>
• /gfilter - <code>ajouter un filtre global</code>
• /gfilters - <code>liste des filtres globaux</code>
• /delg - <code>supprimer un filtre global</code>
• /delallg - <code>supprimer tous les filtres globaux</code>
• /deletefiles - <code>supprimer les fichiers camrip/prédvd</code>
• /send - <code>envoyer un MP à un utilisateur</code>
• /add_premium - <code>ajouter un utilisateur Premium</code>
• /remove_premium - <code>retirer un utilisateur Premium</code>
• /premium_users - <code>liste des utilisateurs Premium</code>
• /get_premium - <code>vérifier les infos Premium</code>
• /restart - <code>redémarrer le bot</code></b>"""

    GROUP_CMD = """<b>👥 Commandes de groupe :

• /settings - <code>configurer les paramètres du groupe</code>
• /set_shortner - <code>définir le 1er raccourcisseur</code>
• /set_shortner_2 - <code>définir le 2ème raccourcisseur</code>
• /set_shortner_3 - <code>définir le 3ème raccourcisseur</code>
• /set_tutorial - <code>définir le 1er tutoriel</code>
• /set_tutorial_2 - <code>définir le 2ème tutoriel</code>
• /set_tutorial_3 - <code>définir le 3ème tutoriel</code>
• /set_time - <code>définir le 1er temps de vérification</code>
• /set_time_2 - <code>définir le 2ème temps de vérification</code>
• /set_log_channel - <code>définir le canal de logs</code>
• /set_fsub - <code>définir l'abonnement forcé</code>
• /reload - <code>connecter votre groupe</code>
• /remove_fsub - <code>supprimer l'abonnement forcé</code>
• /reset_group - <code>réinitialiser les paramètres</code>
• /details - <code>vérifier les paramètres</code></b>"""

    PAGE_TXT = """Pourquoi êtes-vous si curieux ⁉️"""    
   
    SOURCE_TXT = """<b>CODE SOURCE :</b> 👇\nIl s'agit d'un projet open source. Vous pouvez l'utiliser librement, mais la vente du code source est strictement interdite."""