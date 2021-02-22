#Requirements
import time
import os
import random
import discord
import logging

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',level=logging.INFO,datefmt='%Y-%m-%d %H:%M:%S')

#Init
with open("token.txt","r+") as f:
    TOKEN = f.readlines()[0].strip("\n")
botCallCommand = "!tobu "
client = discord.Client() 

#Functions
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
def AddUserCoins(userID,value):
    MakeSureSaveExists(userID)
    save = ReadSaveFile(userID)
    save['coins'] = int(save['coins']) + value
    UpdateSaveFile(userID,save)
def RemoveUserCoins(userID,value):
    if value > 0:
        value = value * -1
    AddUserCoins(userID,value)


#Message event
@client.event
async def on_message(message):
    #If message is from bot: Ignore
    if message.author == client.user:return
    
    try:
        #If the message starts with the bot call command:
        if message.content.lower().startswith(botCallCommand):
            #Command contains the whole message (after removing the bot call command)
            command = message.content[len(botCallCommand):]
            #CommandShort contains the first word after the bot call command
            commandShort = command.split(" ")[0].lower()
            #CommandRest contains the rest (after removing command and commandshort)
            commandRest = command.split(" ")[1:]
            
            messageSenderID = message.author.id
            messageSenderName = message.author.name
            try:
                messageMentionedID = message.mentions[0].id
                messageMentionedName = (await client.fetch_user(messageMentionedID)).name
            except:
                messageMentionedID,messageMentionedName = None,None

            # Command list
            if commandShort == "help":
                # First line of textfile will be the title, and the rest will be the description
                with open("discordhelp.txt",'r') as f:
                    readLines = f.readlines()
                    title = readLines.pop(0).strip("\n")
                    description = "".join(readLines)

                # Gets the current guild, guild icon url and guild name
                currentGuild = client.get_guild(message.guild.id)
                serverIconURL = str(currentGuild.icon_url)
                serverName = currentGuild.name
                
                #Creates embed object
                embed = discord.Embed(
                    color=discord.Colour.from_rgb(154, 0, 255),
                    title=title,
                    description=description
                )
                #Adds server name and icon
                embed.set_author(
                    name=serverName,
                    icon_url=serverIconURL
                )
                await message.channel.send(embed=embed)
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
                    daily = 10

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

                theirCoins = ReadValueInSave(personToStealFromID,'coins')
                if theirCoins == 0:
                    await message.channel.send("bro they broke af, cant steal from them")
                    return

                minStealLimit = 5
                maxStealLimit = round(ReadValueInSave(personToStealFromID,'coins') * 0.3)

                if theirCoins < minStealLimit:
                    minStealLimit = theirCoins
                
                if maxStealLimit > theirCoins:
                    maxStealLimit = theirCoins

                stolenAmmount = random.randint(minStealLimit,maxStealLimit)

                RemoveUserCoins(personToStealFromID,stolenAmmount)
                AddUserCoins(message.author.id,stolenAmmount)

                stealName = (await client.fetch_user(personToStealFromID)).name
                stealerName = message.author.name

                await message.channel.send(f"{stealerName} stole {stolenAmmount} coins from {stealName}!")
                # if random.randint(0,10) <= 3:

                #     RemoveUserCoins(message.author.id,stolenAmmount)
                #     AddUserCoins(personToStealFromID,stolenAmmount)

                #     stealName = message.author.name
                #     stealerName = (await client.fetch_user(personToStealFromID)).name

                #     await message.channel.send(f"{stealName} tried to steal {stolenAmmount} coins from {stealerName}, but they failed, and {stealerName} ended up stealing {stolenAmmount} coins from {stealName} instead!")
                # else:
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

            else:return

    except Exception as e:
        print("ERROR",e);return

#On Load event
@client.event
async def on_ready(): 
    logging.info(f'Logged in as {client.user.name}\n{client.user.id}\n')

#Main
if __name__ == "__main__":
    client.run(TOKEN)
else:
    print("Please run me as Main!")