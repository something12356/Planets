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
    response = requests.get("https://ssd.jpl.nasa.gov/api/horizons.api?format=text&COMMAND='"+target+"'&OBJ_DATA='YES'&MAKE_EPHEM='YES'&EPHEM_TYPE='VECTORS'&START_TIME='"+startTime+"'&STOP_TIME='"+stopTime+"'&CENTER='500@0'&STEP_SIZE='1%20d'&QUANTITIES=''")

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
                ## Mass is in kg, so no multiplying by a factor of 10 is needed
                if response.text[i:i+6].lower() == 'mass x' or response.text[i:i+7].lower() == 'mass, 1' or response.text[i:i+7].lower() == 'mass, x':
                    mass = extractValue(response.text[i:i+50],True)

            ## For some bodies only G*mass, rather than the mass, is given, due to quirks in how we calculate the mass of big things
            ## in this case I have to work out the mass myself from the GM value given.
            ## NASA is not standard AT ALL about how they label the GM value in their ephemeris so I have to have a lot of or statements here
            ## While I do not need this feature at all because I don't include any moons apart from our own,
            ## for users of my program that want to include for example Jupiter's moons, this feature will let them do that.
            else:
                if response.text[i:i+6].lower() == 'gm, km' or response.text[i:i+6].lower() == 'gm   (' or response.text[i:i+6].lower() == 'gm (km':
                    mass = extractValue(response.text[i+20:i+50], False, 1/(6.6743015*10**-20))
            if response.text[i:i+16].lower() == 'vol. mean radius' or response.text[i:i+16].lower() == 'mean radius (km)':
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

## Testing to see if the parser works before implementing it in main program
def main():
    print(getEphemeris(301, True))

if __name__ == "__main__":
    main()