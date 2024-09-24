import requests
import math as maths
response = requests.get("https://ssd.jpl.nasa.gov/api/horizons.api?format=text&COMMAND='499'&OBJ_DATA='YES'&MAKE_EPHEM='YES'&EPHEM_TYPE='VECTORS'&CENTER='500@0'&START_TIME='2006-01-01'&STOP_TIME='2006-01-20'&STEP_SIZE='1%20d'&QUANTITIES='1,9,20,23,24,29'")
print(response.text)

## Sometimes NASA puts a scale next to their units (e.g. they might say mass is measured as 10^23 kg)
## If the scale is expected, it is found and the value is multiplied by it.
## The conversionFactor is because the program works in SI, but NASA sometimes uses kilometres and other non-SI units
## So it converts the unit back to SI
def extractValue(text, expectingScale=False, conversionFactor=1):
    scaleAt = 0
    scale = 1
    if expectingScale:
        for i in range(40):
            if text[i] == '^':
                for j in range(1,25):
                    if not text[i+j].isdigit():
                        scale = eval(text[i-2:i+j].replace('^','**'))
                        break
                scaleAt = i
                break

    ## Once a digit is found it loops until a non-digit character is found. This string is taken to be the value.
    for i in range(scaleAt+3,40):
        if text[i].isdigit():
            for j in range(1,15):
                if i+j >= 40:
                    break
                    print("Parsing error")
                if not text[i+j].isdigit() and text[i+j] not in ['-','.', 'E', '+']:
                    ## This loop removes error margins, not interested, just need a value
                    for k in range(len(text[i:i+j])):
                        if text[i+k:i+k+2] == '+-':
                            j = k
                            break
                    value = float(text[i:i+j])
                    break
            break

    return scale*value*conversionFactor

for i in range(len(response.text)):
    # Mass is in kg, so no multiplying by a factor of 10 is needed
    if response.text[i:i+6] == 'Mass x' or response.text[i:i+5] == 'Mass, ':
        mass = extractValue(response.text[i:i+40],True)
    ## Thankfully volume is the same for both planets and the sun, so it can just be extracted the same way
    if response.text[i:i+16] == 'Vol. mean radius':
        vol = extractValue(response.text[i:i+40], False, 1000)
    
    if response.text[i:i+3] == 'X =':
        posX = extractValue(response.text[i:i+40], False, 1000)
        print(posX)