"""""""""""""""""""""""""""""""""""""""""""""
                   osu!bot
              par Bastien Bodin
           edité la dernière fois
           le 05 mar 2021 à 19h27
"""""""""""""""""""""""""""""""""""""""""""""

from dotenv import load_dotenv # Pour charger notre fichier
import os                      # contenant les ids secrets

import pyosu                   # Osu!API
import discord
from discord.utils import get  # Permet d'utiliser la méthode get() de discord.utils
import random                  # Pour les phrases du bot choisies aléatoirement

# On charge notre .env
load_dotenv()

# Déclaration du bot + ses intents
default_intents = discord.Intents.all()
bot = discord.Client(intents=default_intents)

#On récupère toutes nos informations de notre .env
bot_token = os.getenv("bot_token")
guild_id = int(os.getenv("UID_guild"))
welcome_id = int(os.getenv("UID_welcome"))
mod_newbies_id = int(os.getenv("UID_mod-newbies"))
general_id = int(os.getenv("UID_general"))
osu_client = pyosu.OsuApi(os.getenv("osu_token"))
babibel_id = int(os.getenv("babibel_id")) # ID du développeur du bot

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

    :param member: discord.Member -> Le nouveau membre
    """

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


@bot.event
async def on_raw_reaction_add(payload:discord.RawReactionActionEvent):
    """
    Evênement qui se déclenche quand une/des réaction(s) sont ajoutées sur un message.

    :param payload: discord.RawReactionActionEvent -> toutes les informations qu'on peut récupérer à partir de la réaction
    """

    # Déclaration des variables qu'on utilisera tout le temps
    message_id = payload.message_id
    channel = payload.channel_id
    emote = payload.emoji.name
    reaction_add_member:discord.Member = bot.get_guild(payload.guild_id).get_member(payload.user_id)

    try:
        if channel == mod_newbies_id:
            if emote == "✅":
                for d_id,o_id,m_id,welcome_m_id,r_p in waiting_state_members.values(): # On récupère chaque valeur de chaque membre "en attente"
                    if m_id == message_id: # Si le message dont on a mis ✅ correspond au embed du dit-membre

                        # On déclare toutes les variables dont on a besoin
                        member: discord.Member = bot.get_guild(payload.guild_id).get_member(d_id) # On récupère le membre discord
                        discord_user: discord.User = bot.get_user(member.id)                      # On récupère l'utilisateur discord
                                                                                                  # (à ne pas confondre avec Member qui comporte d'autres méthodes que User)

                        role = get(bot.get_guild(payload.guild_id).roles, name="testrole")        # On récupère le rôle à ajouter
                        member_full_name = f"{discord_user.name}#{discord_user.discriminator}"    # On récupère le nom#tag discord du membre

                        osu_user: pyosu.models.User = await osu_client.get_user(                  # On récupère l'utilisateur osu! grâce à l'ID
                            waiting_state_members[member_full_name][1])                           # stocké dans waiting_state_members

                        new_nick = osu_user.username                                              # On récupère le nom d'utilisateur osu!
                        welcome_msg_id = waiting_state_members[member_full_name][3]               # On récupère l'ID du message envoyé dans #welcome
                        newbies_channel = bot.get_channel(mod_newbies_id)                         # On récupère le channel mod-newbies

                        #On ajoute le rôle au membre + on supprime les messages dans #welcome et #mod-newbies
                        await member.add_roles(role)
                        await bot.http.delete_message(channel, m_id)
                        await bot.http.delete_message(welcome_id,welcome_msg_id)
                        general_channel = bot.get_channel(general_id)

                        # On envoie le embed préparé et on modifie le pseudo du nouvel utilisateur
                        await member.edit(nick=new_nick)

                        newbies_embed = discord.Embed(description=f"{member.nick} a été accepté grâce à {reaction_add_member.display_name} !")

                        await newbies_channel.send(embed=newbies_embed)
                        await member.send("Vous avez été accepté sur le serveur !")
                        await general_channel.send(f"Bienvenue à {member.mention} ! :honk:")
                        del waiting_state_members[member_full_name]
            elif emote == "❌":
                for d_id,o_id,m_id,welcome_m_id,r_p in waiting_state_members.values(): # On récupère chaque valeur de chaque membre "en attente"
                    if m_id == message_id: # Si le message dont on a mis ❌ correspond au embed du dit-membre dans mod-newbies

                        # On déclare toutes les variables dont on a besoin
                        member: discord.Member = bot.get_guild(payload.guild_id).get_member(d_id) # On récupère le membre discord
                        discord_user: discord.User = bot.get_user(member.id)                      # On récupère l'utilisateur discord
                                                                                                  # (à ne pas confondre avec Member qui comporte d'autres méthodes que User)

                        member_full_name = f"{discord_user.name}#{discord_user.discriminator}"    # On récupère le nom#tag discord du membre
                        welcome_channel_id = welcome_id                                           # On récupère le channel welcome
                        welcome_msg_id = waiting_state_members[member_full_name][3]               # On récupère l'ID du message du membre dans #welcome

                        # On supprime les messages dans #welcome et #mod-newbies
                        await bot.http.delete_message(welcome_channel_id, welcome_msg_id)
                        await bot.http.delete_message(channel,m_id)
                        await member.send("Désolé, l'équipe de modération n'a pas accepté votre profil...\n Veuillez quitter le serveur discord. Pour toute réclamation, veuillez contacter un modérateur.")
                        del waiting_state_members[member_full_name]
    except Exception as e:
        print(e.__traceback__.tb_lineno)


@bot.event
async def on_message(message:discord.Message):
    """
    Evênement qui se déclenche quand un message est envoyé sur le serveur ou en MP avec le bot

    :param message: discord.Message -> Le message envoyé + toutes ses caractéristiques
    """
    try:
        if message.channel.id == welcome_id: # On vérifie si le message envoyé est dans le salon welcome

            """
            Algo pour trouver l'url osu! et le stocker:
            
            1°On sépare chaque mot qu'on met dans une liste (message_list)
            2°Pour chaque elément de la liste on regarde si il commence par https://osu.ppy.sh/users/ (ou ..../u/)
            3a°Si 2° est vérifié, alors on resépare chaque portion de l'url dans url_list avec le séparateur "/", pour nous permettre de stocker l'ID osu! en dernière partie
            3b°Si 2° n'est pas vérifié alors on ajoute "?" en réaction au message
            4°On récupère le dernier elément de url_list, qui est donc l'ID osu! du joueur et on le stocke dans new_members à l'endroit du joueur
            5°On exécute la fonction is_osu_user_account_exists (voir plus bas)
            """
            message_list = message.content.split()

            is_verified = False
            for element in range(len(message_list)):
                if message_list[element].startswith("https://osu.ppy.sh/users/") or message_list[element].startswith("https://osu.ppy.sh/u/"):
                    url = message_list[element]
                    url_list = url.split('/')
                    user_id = url_list[-1]
                    new_members[message.author.id][0] = user_id
                    is_verified = True
                    await is_osu_user_account_exists(message.author.id,new_members[message.author.id][0])
            if not is_verified:
                await message.add_reaction("❓")

            # Va enregistrer l'id du message envoyé pour pouvoir le supprimer quand il sera validé
            discord_user: discord.User = message.author
            member_full_name = f"{discord_user.name}#{discord_user.discriminator}"
            waiting_state_members[member_full_name][3] = message.id

        author: discord.User = message.author # Pour vérifier si le message provient d'un bot ou d'un utilisateur
        if message.channel.id == mod_newbies_id and author.bot:
                waiting_state_members[message.embeds[0].author.name][2] = message.id # On récupère l'ID de l'embed du bot pour
                                                                                     # le mettre dans waiting_state_members
                                                                                     # afin de pouvoir le supprimer quand
                                                                                     # le membre sera accepté

        if message.channel.id == mod_newbies_id and not author.bot:
            if message.content.startswith("!rename"): # Vérification de la commande entrée
                # Commande : !rename <discord_id> <new_nick>

                # On rename le membre avec new_nick grâce à son ID discord qui va nous permettre de "récupérer" ce membre
                message_list = message.content.split()
                id = int(message_list[1])
                discord_member:discord.Member = message.guild.get_member(id)
                new_nick = message_list[2]
                await discord_member.edit(nick=new_nick)
                await message.add_reaction("✅") # On rajoute la réaction qui valide le changement

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
                    message_list = message.content.split("-")
                    nick_to_send = message_list[1]
                    message_to_send = f"Babibel répond à {nick_to_send} : {message_list[2]}"
                    newbies_channel = bot.get_channel(mod_newbies_id)
                    await newbies_channel.send(message_to_send)

        if "@Ran" in message.content: # On regarde si Ran est ping
            message_to_send = random.choice(bot_random_answers)
            await message.channel.send(message_to_send)

    except Exception as e:
        print(e.__traceback__.tb_lineno)


async def is_osu_user_account_exists(discord_id, osu_id):
    """
    Fonction qui vérifie que le lien posté dans #welcome est bien valide.
    Si le compte est accessible (= il a bien posté un message dans #welcome), alors on exécute rich_presence_validation.

    :param discord_id: int -> L'ID discord du membre à vérifier
    :param osu_id:     int -> L'ID osu! du membre à vérifier
    """
    if new_members[discord_id][0] is not None: # On check si on a bien l'url dans new_members (évite certains bugs aléatoires)
        user: pyosu.models.User = await osu_client.get_user(osu_id) # Accès à l'utilisateur osu! grâce à son ID
        discord_user:discord.User = bot.get_user(discord_id) # accès à l'utilisateur discord grâce à son ID
        if user: # Si on a bien une réponse de l'API osu!
            discord_user_name = f"{discord_user.name}#{discord_user.discriminator}"
            waiting_state_members[discord_user_name] = [discord_id,osu_id,None,None,True] # None : message du bot associé à l'utilisateur
                                                                                          # None : message posté dans #welcome
                                                                                          # True : on effectue la vérification par rich presence
            del new_members[discord_id] # ça ne sert à rien de garder l'utilisateur dans new_members
            if waiting_state_members[discord_user_name][4]:
                await rich_presence_validation(discord_user)
        else:
            await discord_user.send("Le compte que vous avez posté dans le salon #welcome n'est pas correct.\n"
                                    "Il est possible que vous ayez fait une faute de frappe, merci de réessayer si c'est le cas !")
    else:
        pass


async def rich_presence_validation(discord_user:discord.User):
    """
    Fonction qui envoie un message (embed) pour demander aux modérateurs de valider l'utilisateur ou non

    NE FONCTIONNE PAS SUR LE CHANNEL D'ACCUEIL (celui qui envoie un message dès qu'un nouveau membre arrive

    :param discord_user: discord.User -> L'utilisateur discord et ses caractéristiques
    """

    # Déclaration des variables à utiliser partout
    discord_user_name = f"{discord_user.name}#{discord_user.discriminator}"

    try:
        if waiting_state_members[discord_user_name][2] is None: # Si le bot n'a pas encore posté l'embed dans mod-newbies

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
