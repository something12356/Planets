import requests
import numpy as np
import datetime

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
            for j in range(1,40):
                if i+j >= 40:
                    break
                    print("Parsing error")
                ## The E, + and - being allowed is for scientific notation, because velocity and position,
                ## unlike mass and radius, are presented in scientific notation.
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

def getEphemeris(target):
    target = str(target)
    startTime = datetime.datetime.now().strftime("%Y-%m-%d")
    stopTime = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    response = requests.get("https://ssd.jpl.nasa.gov/api/horizons.api?format=text&COMMAND='"+target+"'&OBJ_DATA='YES'&MAKE_EPHEM='YES'&EPHEM_TYPE='VECTORS'&START_TIME='"+startTime+"'&STOP_TIME='"+stopTime+"'&CENTER='500@0'&STEP_SIZE='1%20d'&QUANTITIES='1,9,20,23,24,29'")
    print(response.text)

    position = np.array([0.0, 0.0, 0.0])
    velocity = np.array([0.0, 0.0, 0.0])
    count = 0

    for i in range(len(response.text)):
        # Mass is in kg, so no multiplying by a factor of 10 is needed
        if response.text[i:i+6].lower() == 'Mass x' or response.text[i:i+5] == 'Mass, ':
            mass = extractValue(response.text[i:i+40],True)
        ## Thankfully radius is the same for both planets and the sun, so it can just be extracted the same way
        if response.text[i:i+16].lower() == 'Vol. mean radius':
            size = extractValue(response.text[i:i+40], False, 1000)
            print("HI!")
        
        if response.text[i:i+3] in ['X =','Y =','Z =','VX=','VY=','VZ=']:
            if count < 3:
                position[count] = extractValue(response.text[i:i+40], False, 1000)
            else:
                velocity[count-3] = extractValue(response.text[i:i+40], False, 1000)
            if count == 5:
            ## NASA provides a list of coordinates of where the planet will be over the
            ## next few days. This is not necessary for our purposes as we just need initial
            ## conditions and then the rest will be simualted from there, so after
            ## the velocity is found, the loop breaks.
                break
            count += 1

    print(velocity)
    return size, velocity, mass, position

print(getEphemeris(10))