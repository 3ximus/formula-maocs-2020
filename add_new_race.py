import json
import sys
import gspread
from oauth2client.service_account import ServiceAccountCredentials

POINT_TABLE = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

if len(sys.argv) == 1:
    print("Give me some file to load.")
    input()
    exit()
else:
    data_file = sys.argv[1]


# SETUP GOOGLE SHEETS
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google_sheets_creds.json", scope)
gsheets_client = gspread.authorize(creds)

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
race = f"Race #{race['ID']}"
race_id = i+2

def miliseconds_to_timing(miliseconds):
    return f"'{miliseconds//1000//60}:{miliseconds//1000%60}:{miliseconds%1000}"

with open(data_file, 'r') as fp:
    race_data = json.load(fp)
    print(race_data['TrackName'])
    input('Press any key to continue...')
    if race_data['Type'] == "RACE":
        print("Uploading RACE")
        race_standings = spread.get_worksheet(2)
        race_times = spread.get_worksheet(3)

        # create lists to index other things
        rs_header = race_standings.row_values(1)
        race_index = rs_header.index(race)+1
        steamids = race_standings.col_values(rs_header.index('Steam ID')+1)

        # update number of laps
        race_standings.update_cell(22, race_index, race_data['RaceLaps'])
        best_lap = 2**32
        best_lap_driver_id = 0
        for i, driver in enumerate(race_data['Result']):
            if driver['TotalTime'] == 0:
                break
            driver_time = miliseconds_to_timing(driver['TotalTime'])
            if driver['BestLap'] < best_lap:
                best_lap = driver['BestLap']
                best_lap_driver_id = driver['DriverGuid']
            print(f"Uploading Driver: {driver['DriverName']} {driver['DriverGuid']} - {driver_time} || BEST_LAP: {miliseconds_to_timing(driver['BestLap'])} || POINTS: {POINT_TABLE[i]}")
            if driver['DriverGuid'] not in steamids:
                print("DriverGuid nof found on sheets.")
                exit()
            driver_index = steamids.index(driver['DriverGuid'])+1
            print(race_standings.cell(driver_index, 1))
            race_standings.update_cell(driver_index, race_index, POINT_TABLE[i])
            race_times.update_cell(driver_index, race_index, driver_time)
        race_times.update_cell(22, race_index, miliseconds_to_timing(best_lap))
        race_times.update_cell(23, race_index, best_lap_driver_id)
        if 'y' in input('Mark Race as finished? (y/n)'):
            spread.get_worksheet(0).update_cell(race_id, 2, True)

    elif race_data['Type'] == "QUALIFY":
        print("Uploading QUALIFY")
        quali_standings = spread.get_worksheet(4)
        quali_times = spread.get_worksheet(5)
        
        # create lists to index other things
        quali_header = quali_standings.row_values(1)
        race_index = quali_header.index(race)+1
        steamids = quali_standings.col_values(quali_header.index('Steam ID')+1)

        best_time = race_data['Result'][0]['BestLap']

        # update things
        for i, driver in enumerate(race_data['Result']):
            # break if there is no total time for driver or the driver has best time than pole position (means this driver didnt set a time)
            if driver['TotalTime'] == 0 or driver['BestLap'] < best_time:
                break
            print(f"Uploading Driver: {driver['DriverName']} {driver['DriverGuid']} || BEST_LAP: {miliseconds_to_timing(driver['BestLap'])}")
            if driver['DriverGuid'] not in steamids:
                print("DriverGuid nof found on sheets.")
                exit()
            driver_index = steamids.index(driver['DriverGuid'])+1
            print(quali_standings.cell(driver_index, 1))
            quali_standings.update_cell(driver_index, race_index, i+1)
            quali_times.update_cell(driver_index, race_index, miliseconds_to_timing(driver['BestLap']))
print("Finished...")
input() # halt program here