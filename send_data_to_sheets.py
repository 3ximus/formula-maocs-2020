from bs4 import BeautifulSoup
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# SETUP GOOGLE SHEETS
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google_sheets_creds.json", scope)
gsheets_client = gspread.authorize(creds)

# Setup headers to parse server manager
headers = requests.utils.default_headers()
headers.update({ 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'})

CHAMPIONSHIP_URL = "http://94.62.85.50:8772/championship/c084c447-0688-4279-a01b-25bd3f5f549f"
ENTRANTS_URL = "http://94.62.85.50:8772/autofill-entrants"
LOGIN_URL = "http://94.62.85.50:8772/login"

payload = {
    'Username':'admin',
    'Password':'frac4ever'
}

drivers = None

with requests.Session() as s:
    # login
    p = s.post(LOGIN_URL, data=payload)
    # get entrants page
    req = s.get(ENTRANTS_URL, headers=headers)
    soup = BeautifulSoup(req.content, 'html.parser')
    table = soup.find('table')
    rows = table.find_all('tr')

    # generate drivers list
    rows = [row.find_all('td') for row in rows]
    drivers = [[e.text.strip() for e in row if e.text.strip()] for row in rows if row]

def get_steam_id(name):
    for driver in drivers:
        if driver[0] == name:
            return driver[-1]

# get championship page
req = requests.get(CHAMPIONSHIP_URL, headers=headers)
soup = BeautifulSoup(req.content, 'html.parser')
table = soup.find('table')
rows = table.find_all('tr')

# generate leaderboard list
rows = [row.find_all('td') for row in rows]
leaderboard = [[e.text.strip() for e in row if e.text.strip()] for row in rows if row]

# parse names, because they have the penalties
for driver in leaderboard: 
    s = driver[1].split('\n')
    driver[1] = s[0]
    if ('Penalty' in s[-1]):
        driver.append(s[-1].strip().split()[-1])

# Grab google sheet
spread = gsheets_client.open("Formula Moacs 2020")
schedule = spread.get_worksheet(0).get_all_records()

race = None
# lookup next race
for i, row in enumerate(schedule):
    if row['Status'] == "FALSE":
        race = row
        break
if not race:	
    print("No more races left in schedule")
    exit()

print(f"Next Race: {race['Name']}")
race_tag = f"Race #{race['ID']}"
race_id = i+2

# find the next race in the html
races = soup.findAll('div', {"class":"card-header"})
for r in races:
    if race['Name'] in r.text:
        if 'Complete' in r.text:
            html_card = r.parent # save the current this html card (race entry in the championship, wtv)
        else:
            print("Next race didn't happen yet. Exiting...")
            exit()
# get data from the tables
results = []
tables = html_card.findAll('table')
for table in tables:
    rows = table.find_all('tr')
    rows = [row.find_all('td') for row in rows]
    results.append([[e.text.strip() for e in row if e.text.strip()] for row in rows if row])

# unpack results
html_qualifying, html_race, html_race_points = results

# streamline names (strip text and fix penalties)
for i in range(len(html_race)):
    s = html_race[i][1].split('\n')
    html_race[i][1] = s[0]
    if 'Penalty' in s[-1]:
        html_race[i].append(s[-1].split()[-1])
    del(html_race[i][3])
    del(html_race[i][4])
    html_race[i][4] = html_race[i][4].split('\n')[0]
    del(html_race[i][5])
    del(html_race[i][5])

for i in range(len(html_qualifying)):
    del(html_qualifying[i][3]) 
    del(html_qualifying[i][4]) 
    del(html_qualifying[i][4]) 
    time, tyre = html_qualifying[i][3].split('\n')
    html_qualifying[i][3] = time
    html_qualifying[i].append(tyre)

# get number of laps
item = html_card.findAll('ul', {'class':'list-unstyled'})[0] # get only the first... the other stuff doesnt matter
li = item.findAll('li')[-1] # get only the race data
row = [r.strip() for r in li.text.split('\n') if r.strip()]
n_laps = row[-1].split()[0]

print(f"Number of laps: {n_laps}")

# get fastest lap name
item = html_card.find('span', {'class':'badge badge-best'})
row = [r.strip() for r in item.text.split('\n') if r.strip()]
fastest_lap_name = row[-1]
fastest_lap_steam_id = get_steam_id(fastest_lap_name)
for q in html_qualifying:
    if q[1] == fastest_lap_name:
        fastest_lap_time = q[3]
print(f"Fastest Lap: {fastest_lap_name} - {fastest_lap_steam_id} - {fastest_lap_time}")
 
# update race sheets
print('Updating Race...')
race_standings = spread.get_worksheet(2)
race_times = spread.get_worksheet(3) 

# create lists to index other things
rs_header = race_standings.row_values(1)
race_index = rs_header.index(race_tag)+1
steamids = race_standings.col_values(rs_header.index('Steam ID')+1)

race_standings.update_cell(22, race_index, n_laps)

for i in range(len(html_race_points)):
    driver = html_race_points[i]
    if get_steam_id(driver[1]) not in steamids:
        print(f'Driver {driver[1]} with steam id: {get_steam_id(driver[1])} not found in sheets. Exiting...')
        exit(1)
    driver_index = steamids.index(get_steam_id(driver[1]))+1
    print(f'Updating driver race data for {driver[1]}')
    race_standings.update_cell(driver_index, race_index, driver[-1])
    time = (html_race[i][3][3:] if html_race[i][3].startswith('00:') else html_race[i][3])
    penalty = f"+{html_race[i][-1]}" if len(html_race[i]) == 6 else ''
    race_times.update_cell(driver_index, race_index, f"'{time} {penalty}")

print('Updating fastest lap data...')
race_times.update_cell(22, race_index, fastest_lap_time)
race_times.update_cell(23, race_index, fastest_lap_steam_id)

# update Qualify sheets
print('Updating Qualify...')
quali_standings = spread.get_worksheet(4)
quali_times = spread.get_worksheet(5)

# create lists to index other things
quali_header = quali_standings.row_values(1)
race_index = quali_header.index(race_tag)+1
steamids = quali_standings.col_values(quali_header.index('Steam ID')+1)

for pos, driver in enumerate(html_qualifying):
    if get_steam_id(driver[1]) not in steamids:
        print(f'Driver {driver[1]} with steam id: {get_steam_id(driver[1])} not found in sheets. Exiting...')
        exit(1)
    driver_index = steamids.index(get_steam_id(driver[1]))+1
    print(f'Updating driver qualify data for {driver[1]}')
    quali_standings.update_cell(driver_index, race_index, pos+1)
    quali_times.update_cell(driver_index, race_index, f"{driver[3]} {driver[4]}")

# update leaderboards
print('Updating Leaderboards...')
names = race_standings.col_values(rs_header.index('Name')+1)
discord_ids = race_standings.col_values(rs_header.index('Discord ID')+1)
teams = race_standings.col_values(rs_header.index('Team')+1)
leaderboard_sheet = spread.get_worksheet(1)
for driver in leaderboard:
    print(f"{driver[1]} {driver[3]}")
    driver_index = steamids.index(get_steam_id(driver[1]))
    leaderboard_sheet.update_cell(int(driver[0])+1, 2, names[driver_index])
    leaderboard_sheet.update_cell(int(driver[0])+1, 3, discord_ids[driver_index])
    leaderboard_sheet.update_cell(int(driver[0])+1, 4, teams[driver_index])
    leaderboard_sheet.update_cell(int(driver[0])+1, 5, driver[3])
    if len(driver) == 5:
        leaderboard_sheet.update_cell(int(driver[0])+1, 6, driver[4])

if 'y' in input('Mark Race as finished? (y/n)'):
    spread.get_worksheet(0).update_cell(race_id, 2, True)