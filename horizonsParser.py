import requests
response = requests.get("https://ssd.jpl.nasa.gov/api/horizons.api?format=text&COMMAND='10'&OBJ_DATA='YES'&MAKE_EPHEM='YES'&EPHEM_TYPE='VECTORS'&CENTER='500@0'&START_TIME='2006-01-01'&STOP_TIME='2006-01-20'&STEP_SIZE='1%20d'&QUANTITIES='1,9,20,23,24,29'&CSV_FORMAT='YES'")
print(response.text)

for i in range(len(response.text)):
    if response.text[i:i+4] == 'Mass':
        print(response.text[i:i+10])