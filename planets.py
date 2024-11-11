import math as maths
import pygame
import numpy as np
import vectors as vec
import horizonsParser

framerate = 120
## Time-scale, how much vel and position should change per tick
## Lower value = slower but more accurate simulation
YEAR = 31536000/framerate
timeScale = 0
## The distance constant is used to translate SI units (metres) into pixels.
## 2 * 10**-12 means that the earth is about 30 pixels from the sun, for reference.
distScale = 4 * 10**-9
zoomScale = distScale
x = 0
y = 1
## Gravitational constant, defines how strong gravity is. Real life G = 6.6743015*10**-11
G = 6.6743015*10**-11

## How long to draw the lines representing the planets' orbits.
MAX_LINES = 300

## Switching from one zoom to another instantly is very jarring. 
## This uses interpolation to smoothly transition between zooms.
## I could use linear interpolation but I actually think this non-linear thing looks nicer so I'm using that.
def zoom(distScale, zoomScale):
    ## No point for the scale to go anywhere near 1000,
    ## so this is in place to prevent any bugs that may occur from zooming in very far
    if distScale*0.9+zoomScale*0.1 > 1000:
        return 1000
    return distScale*0.9 + zoomScale*0.1

## Takes in a position vector and outputs that vector from the centre of mass scaled by the distance constant.
## This way if a planet is 150 million km from the sun, it can be displayed as x amount of pixels from the sun.
def scaledPos(position):
    global planets
    global distScale
    comVector = position - com(planets)
    return com(planets) + distScale * comVector

## Draws an arrow by drawing a line, picking two points either side of that line, and drawing lines from the end of the first line to those two points
def drawArrow(surface, colour, startPos, endPos):
    vector = (endPos - startPos)[:2]
    length = vec.mag(vector)
    ## My solar system is in 3d space, but pygame can only handle 2d lines.
    ## The [:2] is necessary to deal with that.
    pygame.draw.aaline(surface, colour, startPos[:2], endPos[:2])
    ## Generating the two points either side of the line
    norm = vec.normal(vector)
    p1 = startPos[:2] + 0.8*vector[:2] + 0.15*length*norm[:2]
    p2 = startPos[:2] + 0.8*vector[:2] - 0.15*length*norm[:2]
    pygame.draw.aaline(surface, colour, p1, endPos[:2])
    pygame.draw.aaline(surface, colour, p2, endPos[:2])

def displayArrows(planets, adjustment, surface, focus, comFocus):
    ## If no planet is being focused on then there's no arrows to draw
    if comFocus:
        return
    p = planets[focus]
    for arrow in p.getArrows():
        drawArrow(surface, arrow[0], p.getScaledPos()[:2]+adjustment, p.getScaledPos()[:2]+(10**-12)*(distScale)*2*arrow[1][:2]/(maths.log(p.getMass()))+adjustment)

def displayLines(planets, adjustment, focus, comFocus, surface):
    for p in planets:
        index = -1
        orbitalPath = p.getRecords()
        for i in range(len(orbitalPath)-1):
            line = [scaledPos(orbitalPath[i])[:2]+adjustment,scaledPos(orbitalPath[i+1])[:2]+adjustment]
            # print(line[0])
            # print(adjustment)
            # print('---')
            index += 1
            ## Don't draw lines offscreen to avoid lag
            if offscreen(line[0]) and offscreen(line[1]):
                continue
            ## A satellite's lines should not be drawn if its host or itself is not selected
            ## It is unlikely to be visible and will cause lag if drawn
            if p.getHost() != None and (p.getHost() != planets[focus] and p != planets[focus] or comFocus):
                continue
            ## Index ratio is used to reduce opacity and thickness of the older lines 
            ## An index counter is used as python cannot find the index of np arrays with multiple elements
            indexRatio = index/len(orbitalPath)
            pygame.draw.aaline(surface,([int(indexRatio*p.getColour()[i]) for i in range(3)]),line[0],line[1],int(indexRatio*255))
        
def drawPlanet(p, position, surface):
    ## If the planet would fill the whole screen, there's no point trying to draw
    ## more of the circle than necessary, just fill the screen.
    ## This avoids severe lag when zooming in very closely.
    if p.getSize()*distScale > vec.mag(centre):
        screen.fill(p.getColour())
    else:
        pygame.draw.circle(surface,p.getColour(),position,p.getSize()*distScale)
    
## NASA's data on the solar system is all given in 3 dimensional coordinates
## So a simulation of 3d space is used for this program. It also leads to a more accurate model.
## However, displaying 3d graphics is computationally intensive and doesn't contribute to understanding
## of the solar system, so a top down 2d view is displayed. This is why only the first two coordinates of the planet
## are used for drawing it.
def displayPlanets(planets, adjustment, surface):
    for p in planets:
        if offscreen(p.getScaledPos()[:2]+adjustment):
            continue
        drawPlanet(p, p.getScaledPos()[:2]+adjustment, surface)

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
    focusDisplacement = centre - scaledPos(currentFocus)[:2]
    return focusDisplacement

def simulateTick(planets, focus, timeScale):
    for p1 in planets:
        ## Reset energy of planet so it can be recalculated
        p1.addGPE(-p1.getGPE())
        p1.addKE(-p1.getKE())
        p1.addMomentum(-p1.getMomentum())

        ## Takes position before and after so that the lines for the orbits can be drawn
        for p2 in planets[planets.index(p1)+1:]:
            p1gravity = p1.gravity(p2)
            p1.addForce(p1gravity)
            ## Can take away here due to Newton's third law, each force has equal and opposite reaction force
            p2.addForce(-p1gravity)
            ## Draws force arrows showing the forces acting on the planet
            if planets.index(p1) == focus:
                p1.addArrow(["white", np.copy(p1gravity)])
            if planets.index(p2) == focus:
                p2.addArrow(["white", -1*np.copy(p1gravity)])
        if planets.index(p1) == focus:
            p1.addArrow([p1.getColour(), np.copy(p1.getResultant())])
            # arrowsToDraw.append(np.copy(p1.getResultant()))

        p1.secondLaw()
        ## Uses verlet integration to update velocity and acceleration of planet
        p1.verlet(timeScale)
        ## Add a record of the planet's position so we can draw orbital lines.
        p1.addRecord(np.copy(p1.getPos()))
        ## Reset the resultant to 0 so it can be calculated again next tick
        p1.addForce(-p1.getResultant())

## Takes in vector, returns False if within the screen, True otherwise
def offscreen(vector):
    if vector[x] > 0 and vector[x] < 1920 and vector[y] > 0 and vector[y] < 1080:
        return False
    return True

## This is so that the program can demonstrate that momentum and energy are conserved
def sumPhysicalProperties(planets):
    gpe = 0
    ke = 0
    momentum = 0
    for p in planets:
        gpe += p.getGPE()
        ke += p.getKE()
        momentum += p.getMomentum()
    return [gpe, ke, momentum]

class celestialBody:
    def __init__(self, name, size, mass, pos, vel, colour):
        self.__host = None
        self.__name = name
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
        self.__momentum = 0
        self.__records = []
        self.__arrows = []
    
    ## All the getters and setters
    def getHost(self):
        return self.__host

    def getName(self):
        return self.__name

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

    def getMomentum(self):
        return self.__momentum

    def getRecords(self):
        return self.__records

    def getArrows(self):
        return self.__arrows

    def addRecord(self, record):
        self.__records.append(record)
        ## Gets rid of excess lines, prevents them from becoming too long and lagging the system
        if len(self.__records) > LINE_LENGTH:
            self.__records = self.__records[len(self.__records)-LINE_LENGTH:]
    
    def addArrow(self, arrow):
        self.__arrows.append(arrow)
        ## There should never be more than the amount of planets + 1 arrows at a time,
        ## if there are, then some have been left over from previous ticks, and should be cleaned up
        if len(self.__arrows) > len(planets)+1:
            self.__arrows = self.__arrows[len(self.__arrows)-len(planets)-1:]

    ## Adds a force to the resultant force on the planet
    def addForce(self, force):
        self.__resultant += force

    def addGPE(self, energy):
        self.__gpe += energy

    def addKE(self, energy):
        self.__ke += energy

    def addMomentum(self, momentum):
        self.__momentum += momentum

    def addMass(self, mass):
        self.__mass += mass

    ## Sets velocity
    ## Uses F = ma to find acceleration, add to vel
    def secondLaw(self):
        self.__accel = self.getResultant()/self.getMass()
   
    ## Sets position
    ## Updates velocity and then moves a planet by its velocity
    def verlet(self, timeScale):
        self.__vel += self.getAccel()*timeScale
        self.__pos += self.getVel()*timeScale
        self.addKE(0.5*self.getMass()*vec.mag(self.getVel())**2)
        self.addMomentum(self.getMass()*self.getVel())

    ## End of getters and setters

    ## Uses F = GMm/r**2 to work out the force on a planet
    ## Multiplies by unit(r) to make the force a vector.
    def gravity(self, planet2):
        r = planet2.getPos() - self.getPos()
        F = G*(self.getMass()*planet2.getMass())/(vec.mag(r)**2)
        self.addGPE(-F*vec.mag(r))
        planet2.addGPE(F*vec.mag(r))
        return F*vec.unit(r)

## The distinction between planet and satellite here is just whether or not
## they have a specific host. This has no relation to actual planets in real life
## The sun is a planet in my code.
class planet(celestialBody):
    pass

## Satellites (natural like the moon or manmade) show their orbits around their host planet,
## rather than showing their actual path through space like other celestial bodies do.
## This is more useful as it is not easy to see how the satellite orbits its planet otherwise
## The "host" attribute is a planet object, aggregation is used to access the host's attributes
class satellite(celestialBody):
    def __init__(self, name, size, mass, pos, vel, colour, host):
        super().__init__(name, size, mass, pos, vel, colour)
        self.__host = host
        self.__resultant = 0
        self.__records = []

    def getHost(self):
        return self.__host

    ## Adds the host's postion to the line so that it can be displayed, then returns that
    def getRecords(self):
        updatedRecords = [i+self.getHost().getPos() for i in self.__records]
        return updatedRecords

    ## hostLine is the line drawn for the host on the current tick.
    ## Subtracting this from the line for our satellite "removes" the movement of the host.
    ## This leaves only the movement of the satellite around the host.
    def addRecord(self, record):
        hostRecord = self.getHost().getRecords()[-1]
        record = record - hostRecord
        self.__records.append(record)
        if len(self.__records) > LINE_LENGTH:
            self.__records = self.__records[len(self.__records)-LINE_LENGTH:]

## This list contains the name, NASA ID and colour of all the planets
planets = []

planetNames = ["Sun", "Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
planetColours = [(255, 255, 0), (65, 68, 74), (139, 115, 85), (0, 0, 255), (255, 99, 47), (250, 164, 87), (195, 146, 79), (98, 174, 230), (67, 109, 252), (204, 168, 132)]
## I do not want to add all 100+ moons of Jupiter, Saturn, Uranus and Neptune, hence only the important one, our moon, is added
moonColour = (111, 109, 114)
ephemeris = horizonsParser.getEphemeris(10) ## Adding the sun
planets.append(planet(planetNames[0], ephemeris[0], ephemeris[1], ephemeris[2], ephemeris[3], planetColours[0]))
for i in range(1, 10):
    ephemeris = horizonsParser.getEphemeris(i*100+99)
    ## This is adding the moon, it makes sense for it to be just after earth in the planet order
    if i == 4:
        moonEphemeris = horizonsParser.getEphemeris(301)
        planets.append(satellite("Moon", moonEphemeris[0], moonEphemeris[1], moonEphemeris[2], moonEphemeris[3], moonColour, planets[3]))
    ## For some reason, Jupiter's mass is given in grams by NASA
    ## Despite all other masses being given in kilograms
    ## I do not know why
    ## This resolves that problem
    if i == 5:
        ephemeris[1] = ephemeris[1]/1000
    planets.append(planet(planetNames[i], ephemeris[0], ephemeris[1], ephemeris[2], ephemeris[3], planetColours[i]))
# Adding a few prominent satellites (voyager 1&2)
ephemeris=horizonsParser.getEphemeris(-31, False, True, 722, 13) # Voyager 1, need to manually input mass and size as NASA does not provide it
planets.append(planet("Voyager 1", ephemeris[0], ephemeris[1], ephemeris[2], ephemeris[3], moonColour)) ## moonColour is grey, spacecraft are grey, close enough
ephemeris=horizonsParser.getEphemeris(-32, False, True, 722, 13) # Voyager 2
planets.append(planet("Voyager 2", ephemeris[0], ephemeris[1], ephemeris[2], ephemeris[3], moonColour))

## The -3 here is because of the moon, voyager 1 and 2, which are not usually visible and so will not cause extra lag from their orbital paths
LINE_LENGTH = int(MAX_LINES / (len(planets)-3))
pygame.init()
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
## Centre of screen
centre = np.array(pygame.display.get_surface().get_size())/2
clock = pygame.time.Clock()
running = True
arrowsToDraw = []
focus = 0
comFocus = False
arrows = False
comparison = False
planetsToCompare = [3, 4]
comparisonSurface1 = pygame.Surface((957, 1080))
comparisonSurface2 = pygame.Surface((957, 1080))
font = pygame.font.SysFont('codenewroman', 18)
menuSurface1 = pygame.Surface((400, 600), pygame.SRCALPHA)
menuSurface2 = pygame.Surface((400, 600), pygame.SRCALPHA)
menuSurface1.set_alpha(128)
menuSurface2.set_alpha(128)

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

    ## Works out gravitational force between all planets and moves them accordingly each tick
    simulateTick(planets, focus, timeScale)
    distScale = zoom(distScale, zoomScale)
    ## focusAdjustment makes it so that the screen follows whichever planet the user wants to look at
    ## Alternatively, follows the centre of mass, useful for binary star systems
    # focusAdjustment(planets, comFocus)
    if comparison:
        ## These rects get rid of old drawings, similar to doing screen.fill((0,0,0)) to refresh the display
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
        displayLines(planets, focusAdjustment(planets, focus, comFocus), focus, comFocus, screen)
        if arrows:
            displayArrows(planets, focusAdjustment(planets, focus, comFocus), screen, focus, comFocus)

        ## Properties includes the key physical attributes of the system, potential energy, kinetic energy, momenteum
        properties = sumPhysicalProperties(planets)

        ## Displaying the menu
        ## This is absolutely horrible code but it was the best way I could figure out of doing it

        ## Menu surface 1 is for displaying the energies
        ## Menu surface 2 is for the interactive bit, displaying planet info and changing things about the planet / physical constants
        ## The reason I have multiple textSurfaces is because pygame does not seem to support the "\n" character,
        ## so this is the only way I could get new lines.
        pygame.draw.rect(menuSurface1, 'black', (0, 0, 300, 125))
        text1 = "GPE: " + f'{properties[0]:.2e} J'
        text2 = "KE: " + f'{properties[1]:.2e} J'
        text3 = "TOTAL ENERGY: " + f'{properties[0]+properties[1]:.2e} J'
        text4 = "TOTAL MOMENTUM: " + f'{vec.mag(properties[2]):.2e} Ns'
        textSurface1 = font.render(text1, True, (0, 255, 255))
        textSurface2 = font.render(text2, True, (0, 255, 255))
        textSurface3 = font.render(text3, True, (0, 255, 255))
        textSurface4 = font.render(text4, True, (0, 255, 255))
        screen.blit(menuSurface1, (0, 0))
        screen.blit(textSurface1, (20, 20))
        screen.blit(textSurface2, (20, 40))
        screen.blit(textSurface3, (20, 60))
        screen.blit(textSurface4, (20, 80))

        pygame.draw.rect(menuSurface2, 'black', (0, 0, 300, 125))
        ## Display info on current planet as requested by client
        if not comFocus:
            text5 = "OBJECT: " + f'{planets[focus].getName()}'
            text6 = "MASS: " + f'{planets[focus].getMass():.2e} kg'
            text7 = "RADIUS: " + f'{planets[focus].getSize()/1000:.2e} km'
            textSurface5 = font.render(text5, True, (0, 255, 255))
            textSurface6 = font.render(text6, True, (0, 255, 255))
            textSurface7 = font.render(text7, True, (0, 255, 255))
            screen.blit(menuSurface2, (1620, 0))
            screen.blit(textSurface5, (1640, 20))
            screen.blit(textSurface6, (1640, 40))
            screen.blit(textSurface7, (1640, 60))

    pygame.display.flip()
    clock.tick(framerate)