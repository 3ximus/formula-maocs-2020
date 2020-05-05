import discord
from discord.ext import commands

from datetime import datetime

class Standings(commands.Cog):
    TIMING_FORMATS = "%M:%S:%f"
    def __init__(self, bot, spread):
        self.bot = bot
        self.spread = spread
        print("Loading Standings Schedule")
        self.schedule = spread.get_worksheet(0).get_all_records()
        self.leaderboard = spread.get_worksheet(1).get_all_records()
        print("Loading Standings Races Sheets")
        self.race_standings = spread.get_worksheet(2).get_all_records()
        self.race_times = spread.get_worksheet(3).get_all_records()
        print("Loading Standings Qualifyings Sheets")
        self.quali_standings = spread.get_worksheet(4).get_all_records()
        self.quali_times = spread.get_worksheet(5).get_all_records()
        self.last_next_race_message = None

    async def update(self, schedule, standings):
        self.schedule = self.spread.get_worksheet(0).get_all_records()
        self.leaderboard = self.spread.get_worksheet(1).get_all_records()
        self.race_standings = self.spread.get_worksheet(2).get_all_records()
        self.race_times = self.spread.get_worksheet(3).get_all_records()
        self.quali_standings = self.spread.get_worksheet(4).get_all_records()
        self.quali_times = self.spread.get_worksheet(5).get_all_records()
    
    # Commands
    @commands.command(name='standings', aliases=['s', 'leaderboard'])
    async def _standings(self, context):
        """See Standings of the championship"""
        # create embed
        embed = discord.Embed(
            title = "Moaçula 1 Leaderboard",
            colour = discord.Color.dark_red()
        )

        for row in self.leaderboard:
            if row['Name'] == '': break
            user = self.bot.get_user(int(row['Discord ID']))
            embed.add_field(name=f"**#{row['#']}**  {row['Team']}  {row['Name']}",
                            value=f"**{row['Points']}** points  ----  {user.mention}", inline=False)
        
        await context.send(embed=embed)
    
        
    @commands.command(name='last', aliases=['l', 'previous'])
    async def _last_race(self, context, *args):
        """See last race.
            By default it will show race information.
            You can ask Qualifying infomation by adding either 'qualifying' 'quali' or 'q'.
                    ex: !last quali
            You can add a number to show how many races back you want to display.
                    ex: !last 3
            It is also possible to combine the two options:
                    ex: !last 2 qualifying
        """
        done_races = [row for row in self.schedule if row['Status'] == 'TRUE']

        if not done_races:
            await context.send("No race was done yet.")
            return

        n = -1
        for arg in args: # check if argument is number
            if arg.isdecimal():
                n = -int(arg)
        
        if len(done_races) < -n:
            await context.send(f"We didn't do {-n} races yet.")
            return

        race = done_races[n] # nth race back

        # create embed
        embed = discord.Embed(
            title = f"{race['Flag']}  {race['Name']} Grand Prix",
            description = f":date: {race['Date']} : {race['Hora']}",
            colour = discord.Color.dark_red()
        )

        race = f"Race #{race['ID']}"

        if 'qualifying' in args or 'q' in args or 'quali' in args:
            embed = self.generate_qualifying_info(embed, race)
        else:
            embed = self.generate_race_info(embed, race)
            
        await context.send(embed=embed)
    
    def generate_qualifying_info(self, embed, race):
        """Completes embed with Qualifying information of a specific race"""
        race_data = [(st[race], st['Team'], st['Discord ID'], st['Name'], times[race]) for st, times in zip(self.quali_standings, self.quali_times) if st['Name'] != '' and st[race] != '']
        race_data.sort(key=lambda x: x[0])
        embed.description = "==== **Qualifying** ====\n" + embed.description
        
        pole_time = race_data[0][4]
        for i, data in enumerate(race_data):
            user = self.bot.get_user(int(data[2]))
            embed.add_field(name=f"**#{i+1}**  {data[1]}  {data[3]}",
                            value=f"**{self.get_relative_time(pole_time, data[4]) if i != 0 else data[4]}** ---- {user.mention}", inline=False)
        return embed

    def generate_race_info(self, embed, race):
        """Completes embed with Race information of a specific race"""
        race_data = [(st[race], st['Team'], st['Discord ID'], st['Name'], times[race]) for st, times in zip(self.race_standings, self.race_times) if st['Name'] != '' and st[race] != '']
        race_data.sort(key=lambda x: x[0], reverse=True)

        embed.description = f"=== **Race  {self.race_standings[-1][race]} Laps** ===\n" + embed.description
        
        youtube_url = self.race_times[-1][race]
        if (youtube_url != ''):
            embed.url = youtube_url
            embed.set_image(url=f"https://img.youtube.com/vi/{youtube_url[youtube_url.find('v=')+2:]}/mqdefault.jpg")

        winner_time = race_data[0][4]
        for i, data in enumerate(race_data):
            user = self.bot.get_user(int(data[2]))
            embed.add_field(name=f"**#{i+1}**  {data[1]}  {data[3]}  {self.get_relative_time(winner_time, data[4]) if i != 0 else data[4]}",
                            value=f"**{data[0]}** points ---- {user.mention}", inline=False)

        # add fastest lap data
        name = None
        for t in self.race_times:
            if t['Steam ID'] == self.race_times[-2][race]:
                name = t['Name']
                break
        if not name:
            print("Cannot find Steam ID of the fastest lap.")
            return

        embed.add_field(name="Fastest lap  [+1 point]",
                        value=f"**{name}** :stopwatch: {self.race_times[-3][race]}", inline=False)
        return embed

    def get_relative_time(self, base, other):
        b = datetime.strptime(base, self.TIMING_FORMATS)
        o = datetime.strptime(other, self.TIMING_FORMATS)
        result = o - b
        ms = int(str(result.microseconds)[:-3]) if result.microseconds != 0 else 0
        return f"+{result.seconds//60:02d}:{result.seconds%60:02d}:{ms:03d}"





