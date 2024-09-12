import math as maths
import pygame
import numpy as np
import vectors as vec
import physics

## Time-scale, how much vel and position should change per tick
## Lower value = slower but more accurate simulation
YEAR = 315576
timeScale = 1
## The distance constant is used to translate SI units (metres) into pixels.
## 2 * 10**-12 means that the earth is about 30 pixels from the sun.
distScale = 4 * 10**-9
zoomScale = distScale
x = 0
y = 1
## Centre of screen
centre = np.array([960.0,540.0])
## How many orbital lines can be on screen at once
MAX_LINES = 200

## Switching from one zoom to another instantly is very jarring. 
## This uses interpolation to smoothly transition between zooms.
## I could use linear interpolation but I actually think this non-linear thing looks nicer so I'm using that.
def zoom(distScale, zoomScale):
    return distScale*0.9 + zoomScale*0.1

## Takes in a position vector and returns that vector scaled by the log of its distance from the centre of mass.
def logPos(vector, planet=None, takeIntoAccountSize=False, warp=True):
    comVector = vector - com(planets)
    if warp:
        if vec.mag(comVector) > WARP_DISTANCE:
            comVector = comVector - WARP_DISTANCE*vec.unit(comVector)
            if planet == mercury:
                print(vec.mag(comVector))
    # takeIntoAccountSize means that the program considers the distance from the centre of mass
    # to the edge of a planet, rather than its centre.
    if takeIntoAccountSize:
        if vec.mag(comVector) <= planet.getSize():
            if planet == mercury:
                input("")
            comVector = np.array([0.0,0.0])
        else:
            comVector = comVector - planet.getSize()*vec.unit(comVector)
    # if debug:
    #     print(planet.getColour())
    #     print(vec.mag(comVector))
    #     print('---')
    return com(planets) + maths.log(vec.mag(comVector)+1, 10)*vec.unit(comVector)*distScale

## Takes in a position vector and outputs that vector from the centre of mass scaled by the distance constant.
## This way if a planet is 150 million km from the sun, it can be displayed as x amount of pixels from the sun.
def scaledPos(vector):
    comVector = vector - com(planets)
    return com(planets) + distScale * comVector

## Draws an arrow by drawing a line, picking two points either side of that line, and drawing lines from the end of the first line to those two points
def drawArrow(colour, startPos, endPos):
    vector = endPos - startPos
    length = vec.mag(vector)
    pygame.draw.aaline(screen, colour, startPos, endPos)
    ## Generating the two points either side of the line
    norm = vec.normal(vector)
    p1 = startPos + 0.8*vec + 0.15*length*norm
    p2 = startPos + 0.8*vec - 0.15*length*norm
    pygame.draw.aaline(screen, colour, p1, endPos)
    pygame.draw.aaline(screen, colour, p2, endPos)

def displayArrows(arrowsToDraw, adjustment):
    if len(arrowsToDraw) > 0:
        forceToDraw = arrowsToDraw[-1]
    while len(arrowsToDraw) > 1:
        arrow = arrowsToDraw.pop(0)
        p = arrow[1]
        if arrow[0] != "white":
            # print("RESULTANT:", abs(maths.log(vec.mag(forceToDraw)+1,1000))*240*vec.mag(arrow[2]), abs(arrow[3]))
            drawArrow(arrow[0], p.getScaledPos()+adjustment, p.getScaledPos()+(10**-12)*distScale*arrow[2]/(maths.log(p.getMass()))+p.getSize()*distScale*vec.unit(arrow[2])+adjustment)
            print(arrow[2]*distScale*10**-12/(maths.log(p.getMass())))
        else:
            # print("COMPONENT:", abs(maths.log(vec.mag(forceToDraw)+1,1000))*240*vec.mag(arrow[2]), abs(arrow[3]))
            drawArrow(arrow[0], p.getScaledPos()+adjustment, p.getScaledPos()+(10**-12)*distScale*arrow[2]/(maths.log(p.getMass()))+(p.getSize()*distScale)*vec.unit(arrow[2])+adjustment)

def displayLines(planets, adjustment):
    for p in planets:
        for index, line in enumerate(p.getLines()):
            # print(line[0],line[1])
            # print(scaledPos(line[0]))
            if offscreen(scaledPos(line[0])+adjustment) and offscreen(scaledPos(line[1])+adjustment):
                continue
            ## Index ratio is used to reduce opacity and thickness of the older lines 
            ## An index counter is used as python cannot find the index of np arrays with multiple elements
            indexRatio = index/len(p.getLines())
            pygame.draw.aaline(screen,([int(indexRatio*line[2][i]) for i in range(3)]),scaledPos(line[0])+adjustment,scaledPos(line[1])+adjustment,int(indexRatio*255))
        
def displayPlanets(planets, adjustment):
    for p in planets:
        # if offscreen(p.getLogPos()):
        #     continue
        # if p.getColour() == (0,0,255):
        #     print(p.getLogPos())
        ## Don't draw planet if small
        if p.getSize()*distScale > 10**-2:
            pygame.draw.circle(screen,p.getColour(),p.getScaledPos()+adjustment,p.getSize()*distScale)

## Finds the centre of mass of the sysetm
def com(planets):
    com = np.array([0.0,0.0])
    mass = 0
    for p in planets:
        com += p.getMass()*p.getPos()
        mass += p.getMass()
    return com/mass

def focusAdjustment(planets, comFocus, freeCam, camera):
    if freeCam:
        focusDisplacement = centre - camera.getPos()
        print(freeCam)
    else:
        if comFocus:
            focusDisplacement = centre - scaledPos(com(planets))
            print("HII")
        else:
            focusDisplacement = centre - planets[focus].getScaledPos()
    return focusDisplacement
    # for p in planets:
    #     p.move(focusDisplacement)
    #     # print(focusDisplacement)
    #     for line in p.getLines():
    #         line[0] += focusDisplacement
    #         line[1] += focusDisplacement

## Takes in vector, returns False if within the screen, True otherwise
def offscreen(vector):
    if vector[x] > 0 and vector[x] < 1920 and vector[y] > 0 and vector[y] < 1080:
        return False
    return True

class Camera:
    def __init__(self):
        self.__pos = np.array([0.0,0.0])

    def getPos(self):
        return self.__pos

    def setPos(self, pos):
        self.__pos = pos

    def move(self, step):
        self.__pos += step

## All the planets being defined
# sun1 = planet(30,np.array([0.0,0.0]),4000,np.array([960.0,780.0]),(0,255,255))
# sun2 = planet(30,np.array([0.0,0.0]),4000,np.array([960.0,300.0]),(0,255,255))
# # sun3 = planet(30,np.array([0.0,0.0]),4000,np.array([1800.0,540.0]),"red")
# # sun4 = planet(30,np.array([0.0,0.0]),4000,np.array([120.0,540.0]),"red")
# earth = planet(5,np.array([0.3,0.0]),1,np.array([960.0,50.0]),(0,0,255))
# planets = [sun1,sun2,earth]

sun = physics.planet(6.955 * 10**8, np.array([0.0,0.0]),1.99 * 10**30, np.array([960.0, 540.0]),(255,255,0))
mercury = physics.planet(2.440 * 10**6, np.array([0.0, 4.787 * 10**4]), 3.301 * 10**23, np.array([5.791 * 10**10, centre[x]]), (65,68,74))
venus = physics.planet(6.052 * 10**6, np.array([0.0, 3.502 * 10**4]),4.867 * 10**24, np.array([1.08 * 10**11, centre[x]]),(139,115,85))
earth = physics.planet(6.371 * 10 **6,np.array([0.0, 2.978 * 10**4]),5.972 * 10**24, np.array([1.496 * 10**11, centre[x]]),(0,0,255))
moon = physics.satellite(1.738 * 10**6, np.array([0.0, 2.978*10**4+1.022*10**3]),7.348 * 10**22, np.array([1.496 * 10**11 - 3.63*10**8, centre[x]]),(153,153,153), earth)
mars = physics.planet(3.390 * 10**6, np.array([0.0, 2.408 * 10**4]), 6.417 * 10**23, np.array([2.28 * 10**11, centre[x]]), (255,99,47))
jupiter = physics.planet(6.991 * 10**7, np.array([0.0, 1.307 * 10**4]), 1.898 * 10 ** 27, np.array([7.749 * 10**11, centre[x]]), (250, 164, 87))
saturn = physics.planet(5.823 * 10**7, np.array([0.0, 9.69 * 10**3]), 5.683 * 10**26, np.array([1.418 * 10**12, centre[x]]), (195, 146, 79))
uranus = physics.planet(2.536 * 10**7, np.array([0.0, 6.81 * 10**3]), 8.681 * 10**25, np.array([2.9 * 10**12, centre[x]]), (98, 174, 230))
neptune = physics.planet(2.462 * 10**7, np.array([0.0, 5.43 * 10**3]), 1.024 * 10 ** 26, np.array([4.503 * 10**12, centre[x]]), (67, 109, 252))
planets = [sun, mercury, venus, earth, moon, mars, jupiter, saturn, uranus, neptune]
camera = Camera()

## How many orbital lines one planet can have
LINE_LENGTH = int(MAX_LINES / len(planets))
pygame.init()
screen = pygame.display.set_mode((1920,1080))
clock = pygame.time.Clock()
running = True
arrowsToDraw = []
focus = 0
comFocus = False
freeCam = False
arrows = False

while running:
    screen.fill((0,0,0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                focus = (focus+1)%len(planets)
                freeCam = False
            elif event.key == pygame.K_LEFT:
                focus = (focus-1)%len(planets)
                freeCam = False
            elif event.key == pygame.K_UP:
                timeScale += 0.1*YEAR
            elif event.key == pygame.K_DOWN:
                timeScale -= 0.1*YEAR
            elif event.key == pygame.K_SPACE:
                ## Toggles whether or not the screen is centered on the centre of mass
                comFocus = not comFocus
                if freeCam:
                    comFocus = True
                freeCam = False
            elif event.key == pygame.K_f:
                arrows = not arrows
            if event.key == pygame.K_w or event.key == pygame.K_s or event.key == pygame.K_a or event.key == pygame.K_d:
                print('----------')
                print('----------')
                print('----------')
                camera.setPos(centre - focusAdjustment(planets, comFocus, freeCam, camera))
                freeCam = True
        if event.type == pygame.MOUSEWHEEL:
            if event.y == 1:
                if zoomScale < distScale:
                    zoomScale = zoomScale*0.3 + distScale*0.7
                zoomScale += 0.4*zoomScale
            if event.y == -1:
                if zoomScale > distScale:
                    zoomScale = zoomScale*0.3 + distScale*0.7
                zoomScale -= 0.4*zoomScale

    ## Works out gravitational force between all planets and moves them according each tick
    arrowsToDraw = physics.simulateTick(arrowsToDraw, planets, timeScale, focus, comFocus)
    distScale = zoom(distScale, zoomScale)
    ## focusAdjustment makes it so that the screen follows whichever planet the user wants to look at
    ## Alternatively, follows the centre of mass, useful for binary star systems
    # focusAdjustment(planets, comFocus)
    displayLines(planets, focusAdjustment(planets, comFocus, freeCam, camera))
    if arrows:
        displayArrows(arrowsToDraw, focusAdjustment(planets, comFocus, freeCam, camera))
    arrowsToDraw = []
    displayPlanets(planets, focusAdjustment(planets, comFocus, freeCam, camera))

    pygame.display.flip()
    clock.tick(120)