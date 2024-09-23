import math as maths
import pygame
import numpy as np
import vectors as vec

## Time-scale, how much vel and position should change per tick
## Lower value = slower but more accurate simulation
YEAR = 315576
timeScale = 1
## The distance constant is used to translate SI units (metres) into pixels.
## 2 * 10**-12 means that the earth is about 30 pixels from the sun, for reference.
distScale = 4 * 10**-9
zoomScale = distScale
x = 0
y = 1
## Gravitational constant, defines how strong gravity is. Real life G = 
G = 6.6743015*10**-11

## How long to draw the lines representing the planets' orbits.
MAX_LINES = 200

## Centre of screen
centre = np.array([960.0,540.0,0.0])

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
            pygame.draw.aaline(screen,([int(indexRatio*line[2][i]) for i in range(3)]),scaledPos(line[0])[:2]+adjustment[:2],scaledPos(line[1])[:2]+adjustment[:2],int(indexRatio*255))
        
def displayPlanets(planets, adjustment):
    for p in planets:
        # if offscreen(p.getLogPos()):
        #     continue
        # if p.getColour() == (0,0,255):
        #     print(p.getLogPos())
        ## Don't draw planet if small
        if p.getSize()*distScale > 10**-2:
            pygame.draw.circle(screen,p.getColour(),p.getScaledPos()[:2]+adjustment[:2],p.getSize()*distScale)

## Finds the centre of mass of the sysetm
def com(planets):
    com = np.array([0.0,0.0,0.0])
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

def simulateTick(arrowsToDraw, planets, focus, comFocus):
    for p1 in planets:
        ## Takes position before and after so that the lines for the orbits can be drawn
        for p2 in planets[planets.index(p1)+1:]:
            p1p2gravity = p1.gravity(p2)
            p1.addForce(p1p2gravity)

            ## Draws force arrows showing the forces acting on the planet
            if planets.index(p1) == focus and not comFocus:
                arrowsToDraw.append(["white", p1, np.copy(p1p2gravity)])
            if planets.index(p2) == focus and not comFocus:
                arrowsToDraw.append(["white", p2, -1*np.copy(p1p2gravity)])
            ## Can take away here due to Newton's third law, each force has equal and opposite reaction force
            p2.addForce(-p1p2gravity)

        if planets.index(p1) == focus and not comFocus:
            arrowsToDraw.append([p1.getColour(), p1, np.copy(p1.getResultant())])
            arrowsToDraw.append(np.copy(p1.getResultant()))

        p1.secondLaw(p1.getResultant())
        beforePos = np.copy(p1.getPos())
        ## Uses verlet integration to update velocity and acceleration of planet
        p1.verletPosition()
        afterPos = np.copy(p1.getPos())
        p1.addLine([beforePos,afterPos,p1.getColour()])  
        ## Reset the resultant to 0 so it can be calculated again next tick
        p1.addForce(-p1.getResultant())

    return arrowsToDraw

## Takes in vector, returns False if within the screen, True otherwise
def offscreen(vector):
    if vector[x] > 0 and vector[x] < 1920 and vector[y] > 0 and vector[y] < 1080:
        return False
    return True

## NASA's data on the solar system is all given in 3 dimensional coordinates
## So a simulation of 3d space is used for this program. It also leads to a more accurate model.
## However, displaying 3d graphics is computationally intensive. Therefore, a 2d projection is used for display instead.
## The projection itself is rather simple because the chosen plane is the x,y plane. Simply take the x and y coordinates.
## However, planets also need to be shrunk. This is done by calculating their distance to the camera.
## The camera's z position is 960 / d

class Camera:
    def __init__(self):
        self.__pos = np.array([0.0,0.0,0.0])

    def getPos(self):
        return self.__pos

    def setPos(self, pos):
        self.__pos = pos

    def move(self, step):
        self.__pos += step

class celestialBody:
    def __init__(self, size, vel, mass, pos, colour):
        self.__size = size
        self.__vel = vel
        self.__mass = mass
        self.__pos = pos
        self.__colour = colour
        self.__accel = 0
        self.__resultant = 0
        self.__lines = []
    
    ## All the getters and setters
    def getPos(self):
        return self.__pos

    def getLogPos(self):
        ## If the actual distances in our solar system were used, then the either the outer planets would
        ## never be visible, or Earth, Venus and Mercury would look as if they were inside the sun.
        ## Instead, the log of a distance is used. The logarithmic distance of the planets from the sun
        ## increases at a roughly linear rate, making it very easy to display. The centre of mass is
        ## chosen as the centre, as it exists in all star systems, regardless of how many stars they have.
        return logPos(self.getPos(), self, True)

    def getScaledPos(self):
        return scaledPos(self.getPos())

    def getMass(self):
        return self.__mass

    def getVel(self):
        return self.__vel
    
    def getAccel(self):
        return self.__accel

    def getResultant(self):
        return self.__resultant

    def getColour(self):
        return self.__colour

    def getSize(self):
        return self.__size

    def getLines(self):
        return self.__lines

    def addLine(self, line):
        self.__lines.append(line)
        ## Gets rid of excess lines, prevents them from becoming too long and lagging the system
        if len(self.__lines) > LINE_LENGTH:
            self.__lines = self.__lines[len(self.__lines)-LINE_LENGTH:]

    ## Adds a force to the resultant force on the planet
    def addForce(self, force):
        self.__resultant += force

    ## Sets velocity
    ## Uses F = ma to find acceleration, add to vel
    def secondLaw(self, force):
        self.__accel = force/self.getMass()
   
    ## Sets position
    ## Updates velocity and then moves a planet by its velocity
    def verletPosition(self):
        self.__vel += self.getAccel()*timeScale
        self.__pos += self.getVel()*timeScale

    ## End of getters and setters

    ## Uses F = GMm/r**2 to work out the force on a planet
    ## Breaks it into components by doing F*adj/hyp, F*opp/hyp (Fcos(a) and Fsin(a))
    def gravity(self, planet2):
        r = planet2.getPos() - self.getPos()
        F = G*(self.getMass()*planet2.getMass())/(vec.mag(r)**2)
        return np.array([F*i/vec.mag(r) for i in r])

class planet(celestialBody):
    pass

## Satellites (natural like the moon or manmade) show their orbits around their host planet,
## rather than showing their actual pass through space like other celestial bodies do.
## This is more useful as it is not easy to see how the satellite orbits its planet otherwise
## The "host" attribute is a planet object, aggregation is used to access the host's attributes
class satellite(celestialBody):
    def __init__(self, size, vel, mass, pos, colour, host):
        super().__init__(size, vel, mass, pos, colour)
        self.__host = host
        self.__resultant = 0
        self.__lines = []

    def getHost(self):
        return self.__host

    ## Adds the host's postion to the line so that it can be displayed, then returns that
    def getLines(self):
        updatedLines = [[i[j]+self.getHost().getPos() for j in range(2)]+[i[2]] for i in self.__lines]
        return updatedLines

    ## hostLine is the line drawn for the host on the current tick.
    ## Subtracting this from the line for our satellite "removes" the movement of the host.
    ## This leaves only the movement of the satellite around the host.
    def addLine(self, line):
        hostLine = self.getHost().getLines()[-1]
        line[0] = line[0] - hostLine[0]
        line[1] = line[1] - hostLine[1]
        self.__lines.append(line)
        if len(self.__lines) > LINE_LENGTH:
            self.__lines = self.__lines[len(self.__lines)-LINE_LENGTH:]

sun = planet(695700.0 * 10**3, np.array([11.41, -8.292, -0.1685]),1988500.0 * 10 ** 24, np.array([-9.675 * 10 ** 8, -6.663 * 10 ** 8, 2.857 * 10 ** 7]),(255,255,0))
mercury = planet(2.440 * 10**6, np.array([0.0, 4.787 * 10**4, 0.0]), 3.301 * 10**23, np.array([5.791 * 10**10, centre[x], 10000000000.0]), (65,68,74))
# venus = planet(6.052 * 10**6, np.array([0.0, 3.502 * 10**4]),4.867 * 10**24, np.array([1.08 * 10**11, centre[x]]),(139,115,85))
# earth = planet(6.371 * 10 **6,np.array([0.0, 2.978 * 10**4]),5.972 * 10**24, np.array([1.496 * 10**11, centre[x]]),(0,0,255))
# moon = satellite(1.738 * 10**6, np.array([0.0, 2.978*10**4+1.022*10**3]),7.348 * 10**22, np.array([1.496 * 10**11 - 3.63*10**8, centre[x]]),(153,153,153), earth)
# mars = planet(3.390 * 10**6, np.array([0.0, 2.408 * 10**4]), 6.417 * 10**23, np.array([2.28 * 10**11, centre[x]]), (255,99,47))
# jupiter = planet(6.991 * 10**7, np.array([0.0, 1.307 * 10**4]), 1.898 * 10 ** 27, np.array([7.749 * 10**11, centre[x]]), (250, 164, 87))
# saturn = planet(5.823 * 10**7, np.array([0.0, 9.69 * 10**3]), 5.683 * 10**26, np.array([1.418 * 10**12, centre[x]]), (195, 146, 79))
# uranus = planet(2.536 * 10**7, np.array([0.0, 6.81 * 10**3]), 8.681 * 10**25, np.array([2.9 * 10**12, centre[x]]), (98, 174, 230))
# neptune = planet(2.462 * 10**7, np.array([0.0, 5.43 * 10**3]), 1.024 * 10 ** 26, np.array([4.503 * 10**12, centre[x]]), (67, 109, 252))
planets = [sun, mercury]
camera = Camera()

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
    arrowsToDraw = simulateTick(arrowsToDraw, planets, focus, comFocus)
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
    print(mercury.getPos())
    clock.tick(120)