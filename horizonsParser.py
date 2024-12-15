## Program title: Solar System Simulation by Archie Pennycook

import requests
import numpy as np
import datetime

## Sometimes NASA puts a scale next to their units (e.g. they might say mass is measured as 10^23 kg)
## If the scale is expected, it is found and the value is multiplied by it.
## The conversionFactor is because the program works in SI, but NASA sometimes uses kilometres and other non-SI units
## So it converts the unit back to SI
def extractValue(text, expectingScale=False, conversionFactor=1):
    ## scaleAt records the index wher the scale is
    ## So that the second for loop can skip to the position after the scale
    scaleAt = 0
    scale = 1
    ## If there is a scale given (e.g. mass is in 10^24 kg) then it needs to be found
    ## The scale will always include a '^' character, and this does not appear anywhere else in the ephemeris
    ## So this is what is used to search for the scale
    if expectingScale:
        for i in range(50):
            if text[i] == '^':
                for j in range(1,25):
                    if not text[i+j].isdigit():
                        scale = eval(text[i-2:i+j].replace('^','**'))
                        break
                scaleAt = i+j
                break

    ## Once a digit is found it loops until a non-digit character is found. This string is taken to be the value.
    for i in range(scaleAt+1,40):
        ## The text[i] == '-' is so negatives are included
        if text[i].isdigit() or text[i] == '-':
            for j in range(1,50):
                ## Preventing index out of range errors
                if i+j >= 50:
                    break
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

def getEphemeris(target, useGM=False, ignoreMassSize=False, mass=0, size=0):
    target = str(target)
    startTime = datetime.datetime.now().strftime("%Y-%m-%d")
    stopTime = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    ## These request segments only exist to breakup the request so that it is visible in screenshots
    ## As having it all in one line would lead to a very wide screenshot
    ## Which would not be easy to read for the examiner
    requestSegment1 = "https://ssd.jpl.nasa.gov/api/horizons.api?format=text&COMMAND='"
    requestSegment2 = "'&OBJ_DATA='YES'&MAKE_EPHEM='YES'&EPHEM_TYPE='VECTORS'&START_TIME='"
    requestSegment3 = "'&STOP_TIME='"
    requestSegment4 = "'&CENTER='500@0'&STEP_SIZE='1%20d'&QUANTITIES=''"
    response = requests.get(requestSegment1+target+requestSegment2+startTime+requestSegment3+stopTime+requestSegment4)

    position = np.array([0.0, 0.0, 0.0])
    velocity = np.array([0.0, 0.0, 0.0])
    ## The dictionaries are used to ensure we update the correct element of the vector
    posDict = {
        'X =':0,
        'Y =':1,
        'Z =':2,
    }
    velDict = {
        'VX=':0,
        'VY=':1,
        'VZ=':2
    }

    for i in range(len(response.text)):
        ## Sometimes it's convenient to manually set the mass and size, as a lot of the time they're not given by the ephemeris
        ## so that's why ignoreMassSize is a thing
        if not ignoreMassSize:
            if not useGM:
                
                if response.text[i:i+6].lower() == 'mass x' or response.text[i:i+7].lower() in ['mass, 1', 'mass, x']:
                    mass = extractValue(response.text[i:i+50],True) # Mass is in kg, so no multiplying by a factor of 10 is needed

            ## For some bodies only G*mass, rather than the mass, is given, due to quirks in how we calculate the mass of big things
            ## in this case I have to work out the mass myself from the GM value given.
            ## NASA is not standard AT ALL about how they label the GM value in their ephemeris so I use a list with all the possibilities
            ## This is needed for Jupiter's moons
            else:
                if response.text[i:i+6].lower() in ['gm, km', 'gm   (', 'gm (km']:
                    mass = extractValue(response.text[i+20:i+50], False, 1/(6.6743015*10**-20))
            if response.text[i:i+16].lower() in ['vol. mean radius', 'mean radius (km)']:
                size = extractValue(response.text[i:i+50], False, 1000)

        if response.text[i:i+3] in posDict:
            position[posDict[response.text[i:i+3]]] = extractValue(response.text[i:i+40], False, 1000)

        if response.text[i:i+3] in velDict:
            velocity[velDict[response.text[i:i+3]]] = extractValue(response.text[i:i+40], False, 1000)
            ## NASA provides a list of coordinates of where the planet will be over the
            ## next few days. This is not necessary for our purposes as we just need initial
            ## conditions and then the rest will be simulated from there, so after
            ## the final element of velocity is found, the loop breaks.
            if velocity[2] != 0:
                break

    return [size, mass, position, velocity]

## This is used for testing purposes, for test 01
def main():
    ephemeris = getEphemeris(399)
    print("RADIUS:", ephemeris[0], "m")
    print("MASS:", ephemeris[1], "kg")
    print("POSITION:", ephemeris[2])
    print("VELOCITY:", ephemeris[3])

if __name__ == "__main__":
    main()