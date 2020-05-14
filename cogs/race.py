import discord
from discord.ext import commands

class Reaction:
	YES = "\U00002705"
	NO ="\U0000274C" 

# eu, mario, luis
USERS_ALLOWED_TO_SELECT_NEXT_RACE = ['122490947622666242','653739893364883466', '122495338404773894']

class Race(commands.Cog):
    def __init__(self, bot, spread):
        self.bot = bot
        self.spread = spread
        print("Loading Race Schedule")
        self.schedule = spread.get_worksheet(0).get_all_records()
        self.last_next_race_message = None

    async def update(self, schedule):
        self.schedule = self.spread.get_worksheet(0).get_all_records()
    
    # Commands
    @commands.command(name='next', aliases=['n'])
    async def _next_race(self, context):
        """Gives information on the next race"""

        race = None
        # lookup next race
        for row in self.schedule:
            if row['Status'] == "FALSE":
                race = row
                break
        if not race:	
            await context.send("There is no race scheduled...")
            return

        # delete last race message (only if its voting message, generated from an allowed user)
        if str(context.author.id) in USERS_ALLOWED_TO_SELECT_NEXT_RACE and self.last_next_race_message:
            await self.last_next_race_message.delete()
            self.last_next_race_message = None

        # create embed
        embed = discord.Embed(
            title = f"{race['Flag']}  {race['Name']} Grand Prix",
            description = f"{race['Track Name']}\n:date: {race['Date']} : {race['Hora']}",
            colour = discord.Color.dark_red()
        )
        embed.set_image(url=f"https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Racehub%20header%20images%2016x9/{race['Name']}.jpg.transform/9col/image.jpg")
        embed.add_field(name='Members', value='-')
        embed.set_footer(text=f'Download track >>> {race["Link"]}')
        msg = await context.send(embed=embed)

        # limit voting to only these users
        if str(context.author.id) in USERS_ALLOWED_TO_SELECT_NEXT_RACE:
            await msg.add_reaction(Reaction.YES)
            await msg.add_reaction(Reaction.NO)
        self.last_next_race_message = msg

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return
        embed = reaction.message.embeds[0]
        if reaction.emoji == Reaction.YES:
            if str(user.id) not in embed._fields[0]['value']:
                if embed._fields[0]['value'] == "-":
                    embed._fields[0]['value'] = ""
                embed._fields[0]['value'] += f"{user.mention}"
                await reaction.message.edit(embed=embed)
        elif reaction.emoji == Reaction.NO:
            embed._fields[0]['value'] = embed._fields[0]['value'].replace(f"<@!{user.id}>", "")
            if embed._fields[0]['value'] == "":
                embed._fields[0]['value'] = "-"
            await reaction.message.edit(embed=embed)
        else:
            await user.send("Brinca Brinca...")
        await reaction.message.remove_reaction(reaction.emoji, user)


    @commands.command(name='calendar', aliases=['c', 'cal', 'season'])
    async def _calendar(self, context):
        """See Calendar"""

        # create embed
        embed = discord.Embed(
            title = "Moaçula 1 Calendar",
            colour = discord.Color.dark_red()
        )
        
        for race in self.schedule:
            st = '~~' if race['Status'] == 'TRUE' else ''
            date = '*'+race['Date']+'*' if race['Date'] != '' else ''
            embed.add_field(name=f"#{int(race['ID']):02d} {race['Flag']}  {st}{race['Name']}{st}  ",
                            value=f"{st}{race['Track Name']}{st}\n{date}")
        await context.send(embed=embed)

