"""""""""""""""""""""""""""""""""""""""""""""
                   osu!bot
              par Bastien Bodin
           edité la dernière fois
           le 22 fev 2021 à 17h13
              DOC A RENSEIGNER
"""""""""""""""""""""""""""""""""""""""""""""

from dotenv import load_dotenv
import os
import pyosu
import discord
from discord.utils import get
load_dotenv()


bot_token = os.getenv("bot_token")

default_intents = discord.Intents.all()
bot = discord.Client(intents=default_intents)
guild_id = os.getenv("UID_guild")
welcome_id = os.getenv("UID_welcome")
mod_newbies_id = os.getenv("UID_mod-newbies")
osu_client = pyosu.OsuApi(os.getenv("osu_token"))

new_members = {}
waiting_state_members = {}

@bot.event
async def on_ready():
    print("bot prêt")

@bot.event
async def on_member_join(member:discord.Member):
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

    embed.add_field(name="__*Optionel*__: Laissez votre osu! ouvert",
                    value="Si vous avez activé l'option *Discord Rich Presence* sur osu! , "
                          "nous vous invitons à laisser votre jeu osu! ouvert le temps de la vérification.\n",
                    inline=False)

    embed.add_field(name="__Vous ne savez pas comment faire pour l'activer ? Suivez mes instructions (2 min.):__",
                    value="1°Sur le menu principal osu!, allez dans `options`\n"
                          "2°Puis allez dans `Internet`\n"
                          "3°Dans `intégrations` cochez la case `Discord Rich Presence`",
                    inline=False)

    new_members[member.id] = [False,None]
    await member.send(embed=embed)


@bot.event
async def on_raw_reaction_add(payload:discord.RawReactionActionEvent):
    message_id = payload.message_id
    channel = payload.channel_id
    emote = payload.emoji.name
    reaction_add_member:discord.Member = bot.get_guild(payload.guild_id).get_member(payload.user_id)

    if channel == mod_newbies_id:
        if emote == "✅":
            for d_id,o_id,m_id,welcome_m_id,r_p in waiting_state_members.values():
                if m_id == message_id:
                    member = bot.get_guild(payload.guild_id).get_member(d_id)
                    role = get(bot.get_guild(payload.guild_id).roles, name="testrole")
                    discord_user: discord.User = bot.get_user(member.id)
                    member_full_name = f"{discord_user.name}#{discord_user.discriminator}"
                    osu_user: pyosu.models.User = await osu_client.get_user(waiting_state_members[member_full_name][1])
                    new_nick = osu_user.username
                    welcome_channel_id = welcome_id
                    welcome_msg_id = waiting_state_members[member_full_name][3]
                    newbies_channel_id = 700723976141537300
                    newbies_channel = bot.get_channel(newbies_channel_id)
                    newbies_embed = discord.Embed(description=f"{discord_user.name} a été accepté grâce à {reaction_add_member.display_name} !")
                    await member.add_roles(role)
                    await bot.http.delete_message(channel, m_id)
                    await bot.http.delete_message(welcome_channel_id,welcome_msg_id)
                    await newbies_channel.send(embed=newbies_embed)
                    await member.edit(nick=new_nick)
                    await member.send("Vous avez été accepté sur le serveur !")
        elif emote == "❌":
            for d_id,o_id,m_id,welcome_m_id,r_p in waiting_state_members.values():
                if m_id == message_id:
                    member = bot.get_guild(payload.guild_id).get_member(d_id)
                    discord_user: discord.User = bot.get_user(member.id)
                    member_full_name = f"{discord_user.name}#{discord_user.discriminator}"
                    welcome_channel_id = welcome_id
                    welcome_msg_id = waiting_state_members[member_full_name][3]
                    await bot.http.delete_message(welcome_channel_id, welcome_msg_id)
                    await bot.http.delete_message(channel,m_id)
                    await member.send("Désolé, l'équipe de modération n'a pas accepté votre profil...")



@bot.event
async def on_raw_reaction_remove(payload:discord.RawReactionActionEvent):
    pass


@bot.event
async def on_message(message:discord.Message):
    try:
        if message.channel.name == "welcome":
            if not new_members[message.author.id][0]:
                new_members[message.author.id][0] = True
            message_list = message.content.split()
            for element in range(len(message_list)):
                if message_list[element].startswith("https://osu.ppy.sh/users/"):
                    url = message_list[element]
                    url_list = url.split('/')
                    user_id = url_list[-1]
                    new_members[message.author.id][1] = user_id
                    await is_osu_user_account_exists(message.author.id,new_members[message.author.id][1])
                else:
                    await message.add_reaction("❓")
            try:
                discord_user:discord.User = message.author
                member_full_name = f"{discord_user.name}#{discord_user.discriminator}"
                waiting_state_members[member_full_name][3] = message.id
            except KeyError:
                pass

        author: discord.User = message.author
        if message.channel.name == "mod-newbies" and author.bot:
            try:
                waiting_state_members[message.embeds[0].author.name][2] = message.id
            except KeyError:
                pass

        if message.channel.name == "mod-newbies" and not author.bot:
            print("oui")
            print(message.content)
            if message.content.startswith("!rename"):
                print("oui")
                message_list = message.content.split()
                id = int(message_list[1])
                discord_member:discord.Member = bot.get_guild(guild_id).get_member(id)
                new_nick = message_list[2]
                await discord_member.edit(nick=new_nick)
                await message.add_reaction("✅")
    except AttributeError:
        pass


@bot.event
async def on_member_update(before:discord.Member,after:discord.Member):
    discord_user:discord.User = bot.get_user(after.id)
    member_full_name = f"{discord_user.name}#{discord_user.discriminator}"
    try:
        for key in waiting_state_members.keys():
            if key == member_full_name:
                await rich_presence_validation(discord_user)
    except RuntimeError:
        pass



async def is_osu_user_account_exists(discord_id, osu_id):
    if new_members[discord_id][0] and new_members[discord_id][1] is not None:
        user: pyosu.models.User = await osu_client.get_user(osu_id)
        discord_user:discord.User = bot.get_user(discord_id)
        if user:
            discord_user_name = f"{discord_user.name}#{discord_user.discriminator}"
            waiting_state_members[discord_user_name] = [discord_id,osu_id,None,None,True] # None : message du bot associé à l'utilisateur
            if waiting_state_members[discord_user_name][4]:
                await rich_presence_validation(discord_user)
        else:
            await discord_user.send("Le compte que vous avez posté dans le salon #welcome n'est pas correct.\n"
                                    "Il est possible que vous ayez fait une faute de frappe, merci de réessayer si c'est le cas !")
    else:
        print("pas assez d'infos")

async def rich_presence_validation(discord_user:discord.User):
    discord_user_name = f"{discord_user.name}#{discord_user.discriminator}"
    member:discord.Member = bot.get_guild(guild_id).get_member(waiting_state_members[discord_user_name][0])
    verificateur = False

    for activity in member.activities:
        try:
            if activity.application_id == 367827983903490050:
                verificateur = True
                new_nick = activity.assets['large_text'].split()
                role = get(bot.get_guild(guild_id).roles, name="testrole")
                newbies_channel_id = mod_newbies_id
                newbies_channel = bot.get_channel(newbies_channel_id)
                msg_id = waiting_state_members[discord_user_name][2]
                welcome_channel_id = welcome_id
                welcome_msg_id = waiting_state_members[discord_user_name][3]
                await member.edit(nick=new_nick[0])
                await member.add_roles(role)
                try:
                    del waiting_state_members[discord_user_name]
                    await member.send("**Vous avez été accepté sur le serveur!** Merci de votre patience!")
                except KeyError:
                    break
                try:
                    try:
                        await bot.http.delete_message(newbies_channel_id,msg_id)
                        await bot.http.delete_message(welcome_channel_id, welcome_msg_id)
                    except:
                        pass
                    newbies_embed = discord.Embed(description=f"{discord_user_name} a été accepté via Rich Presence !",
                                                  color=discord.Color.dark_teal())
                    newbies_embed.set_footer(text="La technologie c'est vraiment cool")
                    await newbies_channel.send(embed=newbies_embed)
                except discord.errors.NotFound:
                    pass
            else:
                verificateur = False
        except AttributeError:
            pass
    try:
        if not verificateur and waiting_state_members[discord_user_name][2] is None:
            osu_user: pyosu.models.User = await osu_client.get_user(waiting_state_members[discord_user_name][1])

            embed = discord.Embed(description=f"Nouvel utilisateur à vérifier : {osu_user.username}",
                                  color=discord.Color.dark_teal())
            embed.set_author(name=discord_user_name,
                             icon_url=f"https://osu.ppy.sh/a/{waiting_state_members[discord_user_name][1]}",
                             url=f"https://osu.ppy.sh/u/{waiting_state_members[discord_user_name][1]}")
            embed.set_footer(text="Merci d'accepter (ou non) l'utilisateur en utilisant ✔️ ou ❌")

            channel = bot.get_channel(mod_newbies_id)
            await channel.send(embed=embed)
    except KeyError:
        pass


bot.run(bot_token)
