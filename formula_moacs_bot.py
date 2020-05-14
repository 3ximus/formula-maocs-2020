import discord
from discord.ext import commands

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from cogs.race import Race
from cogs.standings import Standings

# Define some constants
with open('discord_token', 'r') as fp:
	TOKEN = fp.read()

# SETUP GOOGLE SHEETS
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google_sheets_creds.json", scope)
gsheets_client = gspread.authorize(creds)

# Grab google sheet
spread = gsheets_client.open("Formula Moacs 2020")

# SETUP DISCORD
discord_client = commands.Bot(command_prefix='!')
race_cog = Race(discord_client, spread)
standings_cog = Standings(discord_client, spread)
discord_client.add_cog(race_cog)
discord_client.add_cog(standings_cog)

@discord_client.event
async def on_ready():
	print('Moacs Ready to Race')

@discord_client.command(name='update')
async def _update(context, *args):
	"""Update the records from google sheets documents into the bot"""
	msg = await context.send("Updating schedule...")
	await race_cog.update(spread.get_worksheet(0))
	await msg.delete()
	msg = await context.send("Updating races...")
	await standings_cog.update(spread.get_worksheet(0), spread.get_worksheet(1))
	await msg.delete()
	await context.send("All done!")

if __name__ == '__main__':
	discord_client.run(TOKEN)