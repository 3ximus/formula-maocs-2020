import urllib

import discord
from discord.ext import commands

def fix_url(url):
    scheme, netloc, path, qs, anchor = urllib.parse.urlsplit(url)
    path = urllib.parse.quote(path, '/%')
    qs = urllib.parse.quote_plus(qs, ':&=')
    return urllib.parse.urlunsplit((scheme, netloc, path, qs, anchor))

class Race(commands.Cog):
    def __init__(self, bot, spread):
        self.bot = bot
        self.spread = spread
        print("Loading Race Schedule")
        self.schedule = spread.get_worksheet(0).get_all_records()

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

        date = ["%02d" % int(x) for x in race['Date'].split('.')]
        date = ''.join(date[::-1])
        time = [int(x) for x in race['Hora'].split(':')]
        timeEnd = [time[0]+1+(time[1]+30)//60, (time[1]+30)%60]
        time=''.join((str(x) for x in time))
        timeEnd=''.join((str(x) for x in timeEnd))
        google_calendar_url = fix_url(f"https://calendar.google.com/calendar/render?action=TEMPLATE&text=Formula Moacs - {race['Name']} Grand Prix&dates={date}T{time}00Z/{date}T{timeEnd}00Z&location={race['Track Name']}%ctz=Europe/Lisbon")

        # create embed
        embed = discord.Embed(
            title = f"{race['Flag']}  {race['Name']} Grand Prix",
            description = f"""{race['Track Name']}
                              > [Download Track]({race['Link']})
                              > [Download Car](https://drive.google.com/file/d/1uNhPY2RhaLBBd3FWUSAKI11w_pESJjsg/view?usp=sharing)
                              
                              [Add event to Google Calendar]({google_calendar_url})
                              """,
            colour = discord.Color.dark_red()
        )
        embed.set_image(url=f"https://www.formula1.com/content/dam/fom-website/2018-redesign-assets/Racehub%20header%20images%2016x9/{race['Name']}.jpg.transform/9col/image.jpg")
        embed.set_footer(text=f"{race['Date']} : {race['Hora']}",
                icon_url='https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/160/openmoji/242/spiral-calendar_1f5d3.png')
        msg = await context.send(embed=embed)

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

