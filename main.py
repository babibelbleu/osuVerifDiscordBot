"""""""""""""""""""""""""""""""""""""""""""""
                   osu!bot
              par Bastien Bodin
           edité la dernière fois
           le 15 mar 2021 à 23h18
"""""""""""""""""""""""""""""""""""""""""""""

from dotenv import load_dotenv # Pour charger notre fichier
import os                      # contenant les ids secrets

import pyosu                   # Osu!API
import discord
from discord.utils import get  # Permet d'utiliser la méthode get() de discord.utils
import random                  # Pour les phrases du bot choisies aléatoirement
import re                      # Pour gérer les regex

# On charge notre .env
load_dotenv()

# Déclaration du bot + ses intents
default_intents = discord.Intents.all()
bot = discord.Client(intents=default_intents)

#On récupère toutes nos informations de notre .env
bot_token = os.getenv("bot_token")
guild_id = int(os.getenv("UID_guild"))
welcome_id = int(os.getenv("UID_welcome"))
mod_newbies_id = int(os.getenv("UID_mod_newbies"))
general_id = int(os.getenv("UID_general"))
osu_client = pyosu.OsuApi(os.getenv("osu_token"))
babibel_id = int(os.getenv("babibel_id"))  # ID du développeur du bot
ran_ping_id = str(os.getenv("ran_mention_id"))  # le message quand on ping le bot (spécifique)
member_role = "testrole"  # Nom du rôle qu'on va ajouter lors de l'acceptation du membre (à changer selon les serveurs)

# Dictionnaires pour stocker les informations de chaque nouveau membre
new_members = {}
waiting_state_members = {}

# Liste de réponses quand le bot est ping
bot_random_answers = ["Ran n'est pas disponible pour le moment. Veuillez ne pas indiquer votre message après le signal sonore.",
                      "Si Sara se casa con la casaca que saca Paca, ni se casa Sara, ni saca la casaca Paca de la saca. :nyab:",
                      "42.",
                      "Vous me le bannez celui qui m'a ping.",
                      "Amusez vous à ping mon créateur mais pas moi, ou sinon sentence irrévocable... AH!",
                      "J'ai pas compris votre demande, veuillez ne jamais la répéter.",
                      "Celui qui m'a ping t'es mort :lazer:",
                      "Atansi0n o phaut de l'ortaugrafe lé anfent, c 1paurtant"]


@bot.event
async def on_ready():
    """
    Evênement qui change l'activité
    du bot et envoie un "bot prêt" en console
    quand le bot est connecté sans erreurs.
    """
    print("bot prêt")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.competing, name="Pourriez-vous stp :nyab:"))


@bot.event
async def on_member_join(member:discord.Member):
    """
    Evênement qui se déclenche quand un membre rejoint le serveur.
    Le nouveau membre va recevoir un embed lui indiquant les étapes à suivre pour s'enregistrer.
    Le membre va être enregistré dans le dictionnaire new_members.

    Si le membre n'a pas ses PM d'activés, un message est alors envoyé aux modérateurs pour leur en indiquer le problème


    Parameters
    ----------
    member: discord.Member
        Le nouveau membre est récupéré

    """

    try:

        # Déclaration du message de bienvenue
        embed = discord.Embed(description="Afin de procéder à la vérification de votre compte, merci de suivre les étapes suivantes:",
                              color=discord.Color.dark_teal())

        embed.set_author(name=f"Bienvenue sur osu!French {member.name} !")
        embed.set_footer(text="Merci pour votre patience et Play more !! :nyab:")

        embed.add_field(name="__Valider le règlement__",
                        value="Vous n'avez qu'à le lire, on vous fait confiance !",
                        inline=True)

        embed.add_field(name="__Indiquer votre profil__",
                        value="Envoyez le lien de votre profil osu! Il ressemble à ça : `https://osu.ppy.sh/users/123456`",
                        inline=True)

        new_members[member.id] = [None] # None  -> L'id osu! de l'utilisateur n'a pas été mis
        await member.send(embed=embed)

    except discord.Forbidden:
        # Déclaration de l'embed qui va indiquer l'erreur aux modérateurs

        user: discord.User = bot.get_user(member.id)  # On a besoin de récupérer un discord.User pour le discriminant

        embed = discord.Embed(description="Merci d'envoyer un message privé à cet utilisateur pour l'accepter !",
                              color=discord.Colour.orange())
        embed.set_author(name=f"Nouvel utilisateur à accepter manuellement : {user.name}#{user.discriminator}")
        channel_to_send = bot.get_channel(mod_newbies_id)
        await channel_to_send.send(embed=embed)


@bot.event
async def on_raw_reaction_add(payload:discord.RawReactionActionEvent):
    """
    Evênement qui se déclenche quand une/des réaction(s) sont ajoutées sur un message.


    Parameters
    ----------
    payload: discord.RawReactionActionEvent
        Toutes les informations qu'on peut récupérer à partir de la réaction : Le membre, l'id du message, etc...

    """

    # Déclaration des variables qu'on utilisera tout le temps
    message_id = payload.message_id
    channel = payload.channel_id
    emote = payload.emoji.name
    reaction_add_member:discord.Member = bot.get_guild(payload.guild_id).get_member(payload.user_id)

    try:
        if channel == mod_newbies_id:
            if emote == "✅":

                # On récupère chaque valeur de chaque membre "en attente"
                for d_id, o_id, m_id, welcome_m_id, r_p in waiting_state_members.values():

                    # Si le message dont on a mis ✅ correspond au embed du dit-membre
                    if m_id == message_id:
                        # On déclare toutes les variables dont on a besoin :

                        # On récupère le membre et l'utilisateur, qui comportent des méthodes différentes
                        member: discord.Member = bot.get_guild(payload.guild_id).get_member(d_id)
                        discord_user: discord.User = bot.get_user(member.id)

                        # On récupère le rôle à ajouter au membre
                        role = get(bot.get_guild(payload.guild_id).roles, name=member_role)

                        # Nom#tag du membre
                        member_full_name = f"{discord_user.name}#{discord_user.discriminator}"

                        # On récupère l'utilisateur osu! grâce à l'ID qu'on a stocké dans waiting_state_members
                        osu_user: pyosu.models.User = await osu_client.get_user(
                            waiting_state_members[member_full_name][1])

                        # Nom d'utilisateur osu!
                        new_nick = osu_user.username

                        # On récupère l'ID du message envoyé par le membre dans #welcome
                        welcome_msg_id = waiting_state_members[member_full_name][3]

                        # On récupère le channel mod-newbies pour envoyer l'embed
                        newbies_channel = bot.get_channel(mod_newbies_id)

                        # On ajoute le rôle au membre + on supprime les messages dans #welcome et #mod-newbies
                        await member.add_roles(role)
                        await bot.http.delete_message(channel, m_id)
                        await bot.http.delete_message(welcome_id,welcome_msg_id)
                        general_channel = bot.get_channel(general_id)

                        # On envoie le embed préparé et on modifie le pseudo du nouvel utilisateur
                        await member.edit(nick=new_nick)

                        newbies_embed = discord.Embed(description=f"{member.nick} a été accepté grâce à"
                                                                  f" {reaction_add_member.display_name} !")

                        await newbies_channel.send(embed=newbies_embed)
                        await member.send("Vous avez été accepté sur le serveur !")
                        await general_channel.send(f"Bienvenue à {member.mention} ! :honk:")
                        del waiting_state_members[member_full_name]

            elif emote == "❌":

                # On récupère chaque valeur de chaque membre "en attente"
                for d_id, o_id, m_id, welcome_m_id, r_p in waiting_state_members.values():
                    # Si le message dont on a mis ❌ correspond au embed du dit-membre
                    if m_id == message_id:

                        # On déclare toutes les variables dont on a besoin
                        # Voir plus haut (if emote == "✅":)  pour le détail de chaque variable
                        member: discord.Member = bot.get_guild(payload.guild_id).get_member(d_id)
                        discord_user: discord.User = bot.get_user(member.id)
                        member_full_name = f"{discord_user.name}#{discord_user.discriminator}"
                        welcome_channel_id = welcome_id
                        welcome_msg_id = waiting_state_members[member_full_name][3]

                        # On supprime les messages dans #welcome et #mod-newbies
                        await bot.http.delete_message(welcome_channel_id, welcome_msg_id)
                        await bot.http.delete_message(channel,m_id)
                        await member.send("Désolé, l'équipe de modération n'a pas accepté votre profil..."
                                          "\n Veuillez quitter le serveur discord."
                                          " Pour toute réclamation, veuillez contacter un modérateur.")
                        del waiting_state_members[member_full_name]
    except Exception as e:
        print(e.__traceback__.tb_lineno)


@bot.event
async def on_message(message:discord.Message):
    """
    Evênement qui se déclenche quand un message est envoyé sur le serveur ou en MP avec le bot


    Parameters
    ----------
    message: discord.Message
        Le message envoyé + toutes ses caractéristiques

    """
    try:

        # On vérifie si le message envoyé est dans le salon welcome
        if message.channel.id == welcome_id: # On vérifie si le message envoyé est dans le salon welcome

            is_verified = False

            # Méthodes du module re (=regex)
            # Besoin de faire deux match puisqu'il existe 2 url différentes à identifier
            match = re.search("https://osu.ppy.sh/users/", message.content)
            match2 = re.search("https://osu.ppy.sh/u/", message.content)

            # Si il y a "match" pour une des deux recherches (si on a trouvé un lien dans le message)
            if match or match2:

                is_verified = True  # L'utilisateur a bien mis un bon lien dans son message
                index_url = match.end()  # Emplacement du caractère de fin du match (dans ce cas il s'agit du '/')

                # On récupère tous les caractères à partir de la position index_url
                user_id = message.content[index_url:]

                new_members[message.author.id][0] = user_id  # On met l'ID récupéré dans new_members
                await is_osu_user_account_exists(message.author.id, new_members[message.author.id][0])

            if not is_verified:
                await message.add_reaction("❓")

            # Va enregistrer l'id du message envoyé pour pouvoir le supprimer quand il sera validé
            discord_user: discord.User = message.author
            member_full_name = f"{discord_user.name}#{discord_user.discriminator}"
            waiting_state_members[member_full_name][3] = message.id

        author: discord.User = message.author # Pour vérifier si le message provient d'un bot ou d'un utilisateur
        if message.channel.id == mod_newbies_id and author.bot:

            # On récupère l'ID de l'embed du bot envoyé pour le mettre dans waiting-state_members
            # afin de pouvoir le supprimer quand le membre sera accepté
            waiting_state_members[message.embeds[0].author.name][2] = message.id

        if message.channel.id == mod_newbies_id and not author.bot:
            if message.content.startswith("!rename"):  # Vérification de la commande entrée
                # Commande : !rename <discord_id> <new_nick>

                # On rename le membre avec new_nick grâce à son ID discord qui va nous permettre de récupérer ce membre
                message_list = message.content.split()
                id = int(message_list[1])
                discord_member: discord.Member = message.guild.get_member(id)
                new_nick = message_list[2]
                await discord_member.edit(nick=new_nick)
                await message.add_reaction("✅")  # On rajoute la réaction qui valide le changement

            if message.content.startswith("!bug"):
                # Commande : !bug <message>

                # On envoie au modérateur du bot le message qui récapitule le bug potentiel
                message_report = message.content[5:]
                member_to_send = bot.get_user(babibel_id)
                member = message.author
                await member_to_send.send(f"Bug trouvé de la part de {member.name} : {message_report}")

        if type(message.channel) == discord.DMChannel: # On vérifie que le message envoyé est bien dans un DM
            if message.author.id == babibel_id:
                if message.content.startswith("!answer"):
                    # Commande : !answer -nick -message

                    # On envoie un -message à -nick dans #mod-newbies

                    # On split le message avec le '-' comme splitter (permet de différencier les arguments entrés)
                    message_list = message.content.split("-")
                    nick_to_send = message_list[1]
                    message_to_send = f"Babibel répond à {nick_to_send} : {message_list[2]}"
                    newbies_channel = bot.get_channel(mod_newbies_id)
                    await newbies_channel.send(message_to_send)

        # On regarde si Ran est ping (le ping renvoie un message spécial ('<@!bot_id>'), et non pas "@Ran")
        if "@Ran" in message.content or ran_ping_id in message.content:
            message_to_send = random.choice(bot_random_answers)
            await message.channel.send(message_to_send)

    except Exception as e:
        print(e.__traceback__.tb_lineno)


async def is_osu_user_account_exists(discord_id, osu_id):
    """
    Fonction qui vérifie que le lien posté dans #welcome est bien valide.
    Si le compte est accessible (= il a bien posté un message dans #welcome), alors on exécute rich_presence_validation.


    Parameters
    ----------
    discord_id: int
        L'ID discord du membre à vérifier

    osu_id: int
        L'ID osu! du membre à vérifier

    """

    # On check si on a bien l'url dans new_members (évite certains bugs aléatoires)
    if new_members[discord_id][0] is not None:

        user: pyosu.models.User = await osu_client.get_user(osu_id)  # Accès à l'utilisateur osu! grâce à son ID
        discord_user:discord.User = bot.get_user(discord_id)  # accès à l'utilisateur discord grâce à son ID

        if user:  # Si on a bien une réponse de l'API osu!

            discord_user_name = f"{discord_user.name}#{discord_user.discriminator}"
            waiting_state_members[discord_user_name] = [discord_id, osu_id, None, None, True]
            # None : message du bot associé à l'utilisateur
            # None : message posté dans #welcome
            # True : on envoie bien l'embed de vérification aux modérateurs (évite certains bugs)

            del new_members[discord_id]  # ça ne sert à rien de garder l'utilisateur dans new_members

            if waiting_state_members[discord_user_name][4]:
                await moderator_validation(discord_user)

        else:  # On n'a pas obtenu de réponse de l'API (profil inexistant ou restricted)
            await discord_user.send("Le compte que vous avez posté dans le salon #welcome n'est pas correct.\n"
                                    "Il est possible que vous ayez fait une faute de frappe, merci de réessayer si c'est le cas !")
    else:
        pass


async def moderator_validation(discord_user:discord.User):
    """
    Fonction qui envoie un message (embed) pour demander aux modérateurs de valider l'utilisateur ou non

    NE FONCTIONNE PAS SUR LE CHANNEL D'ACCUEIL (celui qui envoie un message dès qu'un nouveau membre arrive


    Parameters
    ----------
    discord_user: discord.User
        L'utilisateur discord et ses caractéristiques

    """

    # Déclaration des variables à utiliser partout
    discord_user_name = f"{discord_user.name}#{discord_user.discriminator}"

    try:

        # Si la vérification rich presence n'a pas été effectuée
        # ET que le bot n'a pas encore posté de message dans #mod-newbies
        if waiting_state_members[discord_user_name][2] is None:

            # On récupère l'utilisateur osu! et on envoie l'embed aux modérateurs pour accepter le membre
            osu_user: pyosu.models.User = await osu_client.get_user(waiting_state_members[discord_user_name][1])

            embed = discord.Embed(description=f"Nouvel utilisateur à vérifier : {osu_user.username}",
                                  color=discord.Color.dark_teal())

            embed.set_author(name=discord_user_name,
                             icon_url=f"https://osu.ppy.sh/a/{waiting_state_members[discord_user_name][1]}",
                             url=f"https://osu.ppy.sh/u/{waiting_state_members[discord_user_name][1]}")

            embed.set_footer(text="Merci d'accepter (ou non) l'utilisateur en utilisant ✔️ ou ❌")

            channel = bot.get_channel(mod_newbies_id)
            await channel.send(embed=embed)
    except Exception as e:
        print(e.__traceback__.tb_lineno)

bot.run(bot_token)
