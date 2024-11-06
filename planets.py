import math as maths
import pygame
import numpy as np
import vectors as vec
import horizonsParser

framerate = 120
## Time-scale, how much vel and position should change per tick
## Lower value = slower but more accurate simulation
YEAR = 31536000/framerate
timeScale = 0*YEAR
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

## Takes in a position vector and outputs that vector from the centre of mass scaled by the distance constant.
## This way if a planet is 150 million km from the sun, it can be displayed as x amount of pixels from the sun.
def scaledPos(position):
    global planets
    global distScale
    comVector = position - com(planets)
    return com(planets) + distScale * comVector

## Draws an arrow by drawing a line, picking two points either side of that line, and drawing lines from the end of the first line to those two points
def drawArrow(colour, startPos, endPos):
    vector = (endPos - startPos)[:2]
    length = vec.mag(vector)
    ## My solar system is in 3d space, but pygame can only handle 2d lines.
    ## The [:2] is necessary to deal with that.
    pygame.draw.aaline(screen, colour, startPos[:2], endPos[:2])
    ## Generating the two points either side of the line
    norm = vec.normal(vector)
    p1 = startPos[:2] + 0.8*vector[:2] + 0.15*length*norm[:2]
    p2 = startPos[:2] + 0.8*vector[:2] - 0.15*length*norm[:2]
    pygame.draw.aaline(screen, colour, p1, endPos[:2])
    pygame.draw.aaline(screen, colour, p2, endPos[:2])

def displayArrows(arrowsToDraw, adjustment):
    if len(arrowsToDraw) > 0:
        forceToDraw = arrowsToDraw[-1]
    while len(arrowsToDraw) > 1:
        arrow = arrowsToDraw.pop(0)
        p = arrow[1]
        if arrow[0] != "white":
            drawArrow(arrow[0], p.getScaledPos()+adjustment, p.getScaledPos()+(10**-12)*(distScale)*2*arrow[2]/(maths.log(p.getMass())) + adjustment)
            print(arrow[2]*distScale*10**-12/(maths.log(p.getMass())))
        else:
            drawArrow(arrow[0], p.getScaledPos()+adjustment, p.getScaledPos()+(10**-12)*(distScale)*2*arrow[2]/(maths.log(p.getMass()))+adjustment)

def displayLines(planets, adjustment):
    for p in planets:
        for index, line in enumerate(p.getLines()):
            ## Don't draw line of offscreen to avoid lag
            if offscreen(scaledPos(line[0])+adjustment) and offscreen(scaledPos(line[1])+adjustment):
                continue
            ## Index ratio is used to reduce opacity and thickness of the older lines 
            ## An index counter is used as python cannot find the index of np arrays with multiple elements
            indexRatio = index/len(p.getLines())
            pygame.draw.aaline(screen,([int(indexRatio*line[2][i]) for i in range(3)]),scaledPos(line[0])[:2]+adjustment[:2],scaledPos(line[1])[:2]+adjustment[:2],int(indexRatio*255))
        
def drawPlanet(p, position, surface):
    # if p.getSize()*distScale > 10**-2:
    pygame.draw.circle(surface,p.getColour(),position,p.getSize()*distScale)
    
## NASA's data on the solar system is all given in 3 dimensional coordinates
## So a simulation of 3d space is used for this program. It also leads to a more accurate model.
## However, displaying 3d graphics is computationally intensive and doesn't contribute to understanding
## of the solar system, so a top down 2d view is displayed. This is why only the first two coordinates of the planet
## are used for drawing it.
def displayPlanets(planets, adjustment, surface):
    for p in planets:
        drawPlanet(p, p.getScaledPos()[:2]+adjustment[:2], surface)

## Finds the centre of mass of the sysetm
def com(planets):
    com = np.array([0.0,0.0,0.0])
    mass = 0
    for p in planets:
        com += p.getMass()*p.getPos()
        mass += p.getMass()
    # print(com/mass)
    return com/mass

def focusAdjustment(planets, focus, comFocus):
    if comFocus:
        currentFocus = com(planets)
    else:
        currentFocus = planets[focus].getPos()
    focusDisplacement = centre - scaledPos(currentFocus)
    return focusDisplacement

def simulateTick(arrowsToDraw, planets, focus, comFocus):
    for p1 in planets:
        ## Reset energy of planet so it can be recalculated
        p1.addGPE(-p1.getGPE())
        p1.addKE(-p1.getKE())
        ## Takes position before and after so that the lines for the orbits can be drawn
        for p2 in planets[planets.index(p1)+1:]:
            p1p2gravity = p1.gravity(p2)
            p1.addForce(p1p2gravity)
            ## Can take away here due to Newton's third law, each force has equal and opposite reaction force
            p2.addForce(-p1p2gravity)
            ## Draws force arrows showing the forces acting on the planet
            if planets.index(p1) == focus and not comFocus:
                arrowsToDraw.append(["white", p1, np.copy(p1p2gravity)])
            if planets.index(p2) == focus and not comFocus:
                arrowsToDraw.append(["white", p2, -1*np.copy(p1p2gravity)])


        if planets.index(p1) == focus and not comFocus:
            arrowsToDraw.append([p1.getColour(), p1, np.copy(p1.getResultant())])
            # arrowsToDraw.append(np.copy(p1.getResultant()))

        p1.secondLaw()
        beforePos = np.copy(p1.getPos())
        ## Uses verlet integration to update velocity and acceleration of planet
        p1.verlet()
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

def calculateEnergies(planets):
    gpe = 0
    ke = 0
    for p in planets:
        gpe += p.getGPE()
        ke += p.getKE()
    return [gpe, ke]

class celestialBody:
    def __init__(self, size, vel, mass, pos, colour):
        self.__size = size
        self.__vel = vel
        self.__mass = mass
        self.__pos = pos
        self.__colour = colour
        self.__accel = 0
        self.__resultant = 0
        ## KE and GPE are standard acronyms for kinetic energy and gravitational potential energy
        self.__ke = 0
        self.__gpe = 0
        self.__lines = []
    
    ## All the getters and setters
    def getPos(self):
        return self.__pos

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

    def getGPE(self):
        return self.__gpe

    def getKE(self):
        return self.__ke

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

    def addGPE(self, energy):
        self.__gpe += energy

    def addKE(self, energy):
        self.__ke += energy

    ## Sets velocity
    ## Uses F = ma to find acceleration, add to vel
    def secondLaw(self):
        self.__accel = self.getResultant()/self.getMass()
   
    ## Sets position
    ## Updates velocity and then moves a planet by its velocity
    def verlet(self):
        self.__vel += self.getAccel()*timeScale
        self.__pos += self.getVel()*timeScale
        self.addKE(0.5*self.getMass()*vec.mag(self.getVel())**2)

    ## End of getters and setters

    ## Uses F = GMm/r**2 to work out the force on a planet
    ## Breaks it into components by doing F*adj/hyp, F*opp/hyp (Fcos(a) and Fsin(a))
    def gravity(self, planet2):
        r = planet2.getPos() - self.getPos()
        F = G*(self.getMass()*planet2.getMass())/(vec.mag(r)**2)
        self.addGPE(-1*F*vec.mag(r))
        return np.array([F*i/vec.mag(r) for i in r])

class planet(celestialBody):
    pass

## Satellites (natural like the moon or manmade) show their orbits around their host planet,
## rather than showing their actual path through space like other celestial bodies do.
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

planets = []
planetColours = [(255, 255, 0), (65, 68, 74), (139, 115, 85), (0, 0, 255), (255, 99, 47), (250, 164, 87), (195, 146, 79), (98, 174, 230), (67, 109, 252)]
sunEphemeris = horizonsParser.getEphemeris(10)
planets.append(planet(sunEphemeris[0], sunEphemeris[1], sunEphemeris[2], sunEphemeris[3], planetColours[0]))
for i in range(1, 9):
    ephemeris = horizonsParser.getEphemeris(i*100+99)
    ## For some reason, Jupiter's mass is given in grams by NASA
    ## Despite all other masses being given in kilograms
    ## I do not know why
    ## This resolves that problem
    if i == 5:
        ephemeris[2] = ephemeris[2]/1000
    planets.append(planet(ephemeris[0], ephemeris[1], ephemeris[2], ephemeris[3], planetColours[i]))

LINE_LENGTH = int(MAX_LINES / len(planets))
pygame.init()
screen = pygame.display.set_mode((1920,1080))
clock = pygame.time.Clock()
running = True
arrowsToDraw = []
focus = 0
comFocus = False
arrows = False
comparison = False
planetsToCompare = [0, 5]
comparisonSurface1 = pygame.Surface((957, 1080))
comparisonSurface2 = pygame.Surface((957, 1080))

while running:
    screen.fill((0,0,0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                focus = (focus+1)%len(planets)
            elif event.key == pygame.K_LEFT:
                focus = (focus-1)%len(planets)
            elif event.key == pygame.K_UP:
                timeScale += 0.1*YEAR
            elif event.key == pygame.K_DOWN:
                timeScale -= 0.1*YEAR
            elif event.key == pygame.K_SPACE:
                ## Toggles whether or not the screen is centered on the centre of mass
                comFocus = not comFocus
            elif event.key == pygame.K_f:
                arrows = not arrows
            if event.key == pygame.K_i:
                G += 0.01*G
                print(G)
            if event.key == pygame.K_y:
                if len(planets) == 9:
                    sun = planets[0]
                    planets = planets[1:]
                else:
                    planets.insert(0, sun)
            if event.key == pygame.K_c:
                comparison = not comparison
            if event.key == pygame.K_x:
                planetsToCompare[0] = (planetsToCompare[0]+1) % len(planets)
            if event.key == pygame.K_v:
                planetsToCompare[1] = (planetsToCompare[1]+1) % len(planets)
            
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
    if comparison:
        ## Thes2e rects get rid of old drawings, similar to doing screen.fill((0,0,0)) to refresh the display
        pygame.draw.rect(comparisonSurface1, 'black', (0, 0, 1920, 1080))
        pygame.draw.rect(comparisonSurface2, 'black', (0, 0, 1920, 1080))
        drawPlanet(planets[planetsToCompare[0]], np.array([480, 540]), comparisonSurface1)
        drawPlanet(planets[planetsToCompare[1]], np.array([480, 540]), comparisonSurface2)
        screen.blit(comparisonSurface1, (0, 0))
        screen.blit(comparisonSurface2, (963, 0))
        for i in range(-3,4):
            pygame.draw.aaline(screen, "blue", [960+i,0], [960+i,1080])
    else:
        displayPlanets(planets, focusAdjustment(planets, focus, comFocus), screen)
        displayLines(planets, focusAdjustment(planets, focus, comFocus))
        if arrows:
            displayArrows(arrowsToDraw, focusAdjustment(planets, focus, comFocus))
    energies = calculateEnergies(planets)
    print("GPE:", f'{energies[0]:.2e}')
    print("KE:", f'{energies[1]:.2e}')
    print("TOTAL:", f'{energies[0]+energies[1]:.2e}')
    print('---')

    pygame.display.flip()
    clock.tick(framerate)