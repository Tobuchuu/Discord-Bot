#Requirements
import time
import os
import random
import discord
import logging
import re
import json

from discord.activity import Streaming

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',level=logging.INFO,datefmt='%Y-%m-%d %H:%M:%S')

#Init
with open("token.txt","r+") as f:
    TOKEN = f.readlines()[0].strip("\n")
botCallCommand = "!tim "

intents = discord.Intents.all()
intents.message_content = True

client = discord.Client(intents=intents) 

# region - Functions
def MakeSureSaveExists(userID):
    fileExists = os.path.isfile(f"save/{str(userID)}.txt")
    if not fileExists:
        with open(f'save/{str(userID)}.txt','w') as f:
            saveDefault = {'coins':0}
            for key in saveDefault:
                f.write(f"{key} = {saveDefault[key]}\n")
def ReadSaveFile(userID):
    MakeSureSaveExists(userID)
    toReturn = {}
    with open(f'save/{str(userID)}.txt','r') as f:
        for x in f.readlines():
            theSplit = x.strip('\n').split(' = ')
            toReturn[theSplit[0]] = theSplit[1]
    return toReturn
def UpdateSaveFile(userID,dict):
    MakeSureSaveExists(userID)
    with open(f'save/{str(userID)}.txt','w') as f:
        for key in dict:
            f.write(f"{key} = {dict[key]}\n")
def ChangeValueInSave(userID,dict):
    MakeSureSaveExists(userID)
    save = ReadSaveFile(userID)
    for key in dict:
        save[key] = dict[key]
    UpdateSaveFile(userID,save)
def ReadValueInSave(userID,valueName):
    MakeSureSaveExists(userID)
    save = ReadSaveFile(userID)
    try:
        return save[valueName]
    except:
        return None
def DeleteValueInSave(userID,valueName):
    MakeSureSaveExists(userID)
    save = ReadSaveFile(userID)
    newSave = {}
    for key in save:
        if key in valueName:
            continue
        newSave[key] = save[key]
    UpdateSaveFile(userID,newSave)
def AddUserCoins(userID,value):
    MakeSureSaveExists(userID)
    save = ReadSaveFile(userID)
    save['coins'] = int(save['coins']) + value
    UpdateSaveFile(userID,save)
def RemoveUserCoins(userID,value):
    if value > 0:
        value = value * -1
    AddUserCoins(userID,value)

# endregion

#Message event
@client.event
async def on_message(message):
    #If message is from bot: Ignore
    if message.author == client.user:return

    messageSenderID = message.author.id
    messageSenderName = message.author.name
    try:
        messageMentionedID = message.mentions[0].id
        messageMentionedName = (await client.fetch_user(messageMentionedID)).name
    except:
        messageMentionedID,messageMentionedName = None,None
    
    
    try:
        #If the message starts with the bot call command:
        if message.content.lower().startswith(botCallCommand):
            #Command contains the whole message (after removing the bot call command)
            command = message.content[len(botCallCommand):]
            #CommandShort contains the first word after the bot call command
            commandShort = command.split(" ")[0].lower()
            #CommandRest contains the rest (after removing command and commandshort)
            commandRest = command.split(" ")[1:]
            
            # Command list
            if commandShort == "help":
                # First line of textfile will be the title, and the rest will be the description
                with open("discordhelp.txt",'r') as f:
                    readLines = f.readlines()
                    title = readLines.pop(0).strip("\n")
                    description = "".join(readLines)

                # Gets the current guild, guild icon url and guild name
                currentGuild = client.get_guild(message.guild.id)
                serverIconURL = str(currentGuild.icon)
                serverName = currentGuild.name
                
                #Creates embed object
                embed = discord.Embed(
                    color=discord.Colour.from_rgb(203, 15, 15),
                    title=title,
                    description=description
                )
                #Adds server name and icon
                embed.set_author(
                    name=serverName,
                    icon_url=serverIconURL
                )
                await message.channel.send(embed=embed)
            
            #--------------------------------coin system---------------------------
            elif commandShort == "daily":
                # If message contains mentions, then it will instead only report how much time that person has left on their daily timer
                try:
                    theId = message.mentions[0].id
                    try:
                        lastTimeDailyClaimed = float(ReadValueInSave(theId,'dailyTimer'))
                        
                        if time.time()-lastTimeDailyClaimed > 86400:
                            await message.channel.send(f"{(await client.fetch_user(theId)).name} can claim their daily!")
                        else:
                            timeUntillCanClaimAgain = 86400 - (time.time() - lastTimeDailyClaimed)
                            await message.channel.send(f"{(await client.fetch_user(theId)).name} has to wait **{time.strftime('%H hours, %M minutes and %S secounds', time.gmtime(timeUntillCanClaimAgain))}** before they can claim their daily!")
                    except:
                        await message.channel.send(f"{(await client.fetch_user(theId)).name} has never claimed their daily!")
                # If not, then it will instaed attempt to claim your daily
                except:
                    daily = random.randint(10,100)

                    # Loads the timestamp saved in 'dailyTimer'
                    lastTimeDailyClaimed = ReadValueInSave(message.author.id,'dailyTimer')

                    # None means that the user has never claimed their daily
                    # Arg2 is true if the saved timestamp is 24 hours old or older
                    # So if True, then you are able to claim your daily
                    if lastTimeDailyClaimed == None or time.time()-float(lastTimeDailyClaimed) > 86400:
                        # Adds the coins to your save
                        AddUserCoins(message.author.id,daily)
                        # Updates the dailyTimer with the current timestamp
                        ChangeValueInSave(message.author.id,{'dailyTimer':time.time()})
                        await message.channel.send(f"You claimed your daily and earned yourself {daily} coins! You now have {ReadValueInSave(message.author.id,'coins')} coins!")
                    else:
                        # Else, it will tell you how much time you have left untill you can claim
                        timeSince = 86400 - (time.time() - float(lastTimeDailyClaimed))
                        await message.channel.send(f"You can't claim your daily yet! You have to wait **{time.strftime('%H hours, %M minutes and %S secounds', time.gmtime(timeSince))}**!")            
            elif commandShort in ("balance","bal","coins"):
                try:
                    theId = message.mentions[0].id
                    await message.channel.send(f"{(await client.fetch_user(theId)).name} has {ReadValueInSave(theId,'coins')} coins!")
                except:
                    await message.channel.send(f"You have {ReadValueInSave(message.author.id,'coins')} coins!")
            elif commandShort == "steal":
                personToStealFromID = message.mentions[0].id

                if personToStealFromID == messageSenderID:
                    await message.channel.send("Why are you trying to steal from yourself dumbass?")
                    return

                theirCoins = int(ReadValueInSave(personToStealFromID,'coins'))
                if theirCoins <= 17:
                    await message.channel.send("bro they broke af, cant steal from them")
                    return

                minStealLimit = 5
                maxStealLimit = round(float(ReadValueInSave(personToStealFromID,'coins')) * 0.3)

                if theirCoins < minStealLimit:
                    minStealLimit = theirCoins
                
                if maxStealLimit > theirCoins:
                    maxStealLimit = theirCoins

                stolenAmmount = random.randint(minStealLimit,maxStealLimit)

                if random.randint(0,10) >= 4:
                    RemoveUserCoins(personToStealFromID,stolenAmmount)
                    AddUserCoins(message.author.id,stolenAmmount)

                    stealName = (await client.fetch_user(personToStealFromID)).name
                    stealerName = message.author.name

                    await message.channel.send(f"{stealerName} stole {stolenAmmount} coins from {stealName}!")
                else:
                    RemoveUserCoins(message.author.id,stolenAmmount)
                    AddUserCoins(personToStealFromID,stolenAmmount)

                    stealName = message.author.name
                    stealerName = (await client.fetch_user(personToStealFromID)).name

                    await message.channel.send(f"**{stealName}** tried to steal **{stolenAmmount} coins** from **{stealerName}** but got caught in 4K 📷. Now they have to pay **{stealerName} {stolenAmmount} coins** instead!")

            elif commandShort in ("transfer","trans","send"):
                try:
                    if messageMentionedID != None:
                        transferAmmount = int(commandRest[0])

                        if int(ReadValueInSave(messageSenderID,'coins')) >= transferAmmount:
                            RemoveUserCoins(messageSenderID,transferAmmount)
                            AddUserCoins(messageMentionedID,transferAmmount)
                            await message.channel.send(f"{messageSenderName} sent {messageMentionedName} {transferAmmount} {'coin'if transferAmmount==1 else'coins'}!")
                        else:
                            await message.channel.send(f"You do not have {transferAmmount} {'coin'if transferAmmount==1 else'coins'}!")
                    else:
                        await message.channel.send("You have to @ the person you want to send coins too!")
                except:
                    await message.channel.send("You have to specify how much you want to send!")
            elif commandShort == "coinflip":
                try:
                    bet = int(commandRest[0])

                    if int(ReadValueInSave(message.author.id,'coins')) >= bet:

                        RemoveUserCoins(message.author.id,bet)

                        loadingMessage = await message.channel.send("Flipping coin...")

                        time.sleep(3)

                        if random.randint(0,10) <= 5:
                            AddUserCoins(message.author.id,bet*2)
                            await loadingMessage.edit(content=f"You won {bet*2} coins!")
                        else:
                            await loadingMessage.edit(content=f"You lost {bet} {'coin'if bet==1 else'coins'}... better luck next time!")
                    else:
                        await message.channel.send(f"You do not have {bet} {'coin'if bet==1 else'coins'}!")
                except:
                    await message.channel.send("You have to specify how much you want to bet!")
            elif commandShort in ("guess.the.number", "guessnum"):
                if ReadValueInSave(messageSenderID,'gameRunning') == "1":
                    return
                ChangeValueInSave(messageSenderID,{'gameRunning':"1"})
                ChangeValueInSave(messageSenderID,{'game_tries':3})
                ChangeValueInSave(messageSenderID,{'game_randomNumber':random.randint(0,100)})
                ChangeValueInSave(messageSenderID,{'game_timer':time.time()})
                await message.channel.send("Guess a number between 0 to 100! You have 3 tries and a timer of 1 minute")
                print(ReadValueInSave(messageSenderID,'game_randomNumber'))
                #while (player.message.content != randomNumber and tries != 0 and time.time()-float(timer) > 60):
            elif commandShort == "hangman":
                await message.channel.send("wip...")
            elif commandShort == "echo":
                message = await message.channel.send(" ".join(commandRest))
                await message.channel.send(message.id)
                
            else:return
            return

        if ReadValueInSave(messageSenderID,'gameRunning') == "1":
            def CleanUpAfterGameOver():
                DeleteValueInSave(messageSenderID,('gameRunning','game_tries', 'game_randomNumber', 'game_timer'))

        try:
            int(message.content)
            if time.time() - float(ReadValueInSave(messageSenderID,'game_timer')) < 60:
                if message.content == ReadValueInSave(messageSenderID,'game_randomNumber'):
                    await message.channel.send("You are win! The number was **" + ReadValueInSave(messageSenderID,'game_randomNumber') + "**\nYou earned 30 coins.")
                    CleanUpAfterGameOver()
                    AddUserCoins(messageSenderID, 30)
                else:
                    triesLeft = int(ReadValueInSave(messageSenderID,'game_tries')) - 1
                    if triesLeft == 0:
                        await message.channel.send("You used up all your tries.")
                        await message.channel.send("The number was **" + ReadValueInSave(messageSenderID,'game_randomNumber') + "**")
                        CleanUpAfterGameOver()
                    else:
                        if message.content > ReadValueInSave(messageSenderID,'game_randomNumber'):
                            await message.channel.send("You guessed too high.")
                        else:
                            await message.channel.send("You guessed too low.")
                        await message.channel.send(f"You have {triesLeft} tries left.")
                        ChangeValueInSave(messageSenderID,{'game_tries':triesLeft})
            else:
                await message.channel.send("The number was **" + ReadValueInSave(messageSenderID,'game_randomNumber') + "**")
                await message.channel.send("Time's is up!")
                CleanUpAfterGameOver()
        except:
            pass 

    except Exception as e:
        print("ERROR",e);return



# region - Self roles
class ReactionSaveFile:
    def __init__(self, guild_id) -> None:
        self.guild_id = guild_id
        self.__fn = f"data/{self.guild_id}.json"

    def _load(self):
        if os.path.isfile(self.__fn):
            with open(self.__fn , "r", encoding="utf-8") as f:
                self.__guild_data = json.load(f)
        else:
            self.__guild_data = {
                "message_ids": [],
                "roles": {}
            }
    
    def _save(self):
        with open(self.__fn , "w", encoding="utf-8") as f:
            json.dump(self.__guild_data, f,  ensure_ascii=False, indent=4)
    
    def add_message_id(self, message_id):
        self._load()
        if not message_id in self.__guild_data["message_ids"]:
            self.__guild_data["message_ids"].append(int(message_id))
        self._save()
    def remove_message_id(self, message_id):
        self._load()
        self.__guild_data["message_ids"] = [x for x in self.__guild_data["message_ids"] if x != int(message_id)]
        self._save()

    def add_role(self, emoji, role_name, description=None):
        self._load()
        self.__guild_data["roles"][emoji] = {"role_name": role_name, "description": description}
        self._save()
    def remove_role(self, emoji):
        self._load()
        if emoji in self.__guild_data["roles"]:
            del self.__guild_data["roles"][emoji]
        self._save()

    def get_guild_data(self):
        self._load()
        return self.__guild_data


async def get_reaction_from_payload(payload, action):
    message_id = payload.message_id
    guild_id = payload.guild_id

    guild_data = ReactionSaveFile(guild_id).get_guild_data()

    if message_id in guild_data["message_ids"]:
        guild = discord.utils.find(lambda g : g.id == guild_id, client.guilds)

        if payload.emoji.name in guild_data["roles"]:
            role = discord.utils.get(guild.roles, name=guild_data["roles"][payload.emoji.name]["role_name"])
        else:
            role = discord.utils.get(guild.roles, name=payload.emoji.name)

        if role is not None:
            member = discord.utils.find(lambda m : m.id == payload.user_id, guild.members)
            if member is not None:
                if action == "+":
                    await member.add_roles(role)  
                elif action == "-":
                    await member.remove_roles(role)

@client.event
async def on_raw_reaction_add(payload):
    try:
        if payload.member == client.user:return
    except:pass
    await get_reaction_from_payload(payload, "+")

@client.event
async def on_raw_reaction_remove(payload):
    try:
        if payload.member == client.user:return
    except:pass
    await get_reaction_from_payload(payload, "-")
# endregion


@client.event
async def on_message(payload):
    if payload.author == client.user:return

    guild_id = payload.guild.id
    role_handler = ReactionSaveFile(guild_id)

    regex_template = f"{re.escape(botCallCommand)}[^ ]* "
    
    if payload.content.lower() == botCallCommand+"display":
        roles = role_handler.get_guild_data()["roles"]
        msg = ""
        for role in roles:
            msg += role + " : `"+roles[role]["role_name"]+ "`"
            if roles[role]["description"] != None:
                msg += " - "+roles[role]["description"] 
            msg += "\n"

        # Gets the current guild, guild icon url and guild name
        currentGuild = client.get_guild(payload.guild.id)
        serverIconURL = str(currentGuild.icon)
        serverName = currentGuild.name
        
        #Creates embed object
        embed = discord.Embed(
            color=discord.Colour.from_rgb(203, 15, 15),
            title="Role Menu: React to give yourself a role.",
            description=msg
        )
        #Adds server name and icon
        embed.set_author(
            name=serverName,
            icon_url=serverIconURL
        )
        r = await payload.channel.send(embed=embed)
        role_handler.add_message_id(r.id)
        for x in roles:
            try:
                # TODO make the stupid robot send the correct emoji and shit from custom emojis yes
                # i dunno man just find a fucntion that does the thing and work and 
                # Make it work with Custom emojis 
                # I love you baby
       
                await r.add_reaction(x)
            except:
                pass
    elif payload.content.lower().startswith(botCallCommand+"add"):
        response = re.findall(regex_template+'([^ "]*) "([^"]*)"(?: "([^"]*)")?', payload.content)
        if len(response) > 0:
            response = response[0]
            role_handler.add_role(emoji=response[0], role_name=response[1], description=response[2])
    elif payload.content.lower().startswith(botCallCommand+"remove"):
        response = re.findall(regex_template+'([^ "]*)', payload.content)
        if len(response) > 0:
            role_handler.remove_role(emoji=response[0])

#On Load event
@client.event
async def on_ready(): 
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.streaming, name="!tim help", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
    logging.info(f'Logged in as {client.user.name}\t{client.user.id}\n')

#Main
if __name__ == "__main__":
    if not os.path.exists("./data/"): os.mkdir("data")
    client.run(TOKEN)
else:
    print("Please run me as Main!")