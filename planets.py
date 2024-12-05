import math as maths
import pygame
import numpy as np
import vectors as vec
import horizonsParser

### These are all either constants or are variables that are only ever changed by main(), and so
### it's okay to define them here and use them globally.
## The distance constant is used to translate SI units (metres) into pixels.
## 4 * 10**-9 means that the earth is about 600 pixels from the sun, for reference.
distScale = 4 * 10**-9
zoomScale = distScale
x = 0
y = 1

## Gravitational constant, defines how strong gravity is. Real life G = 6.6743015*10**-11
G = 6.6743015*10**-11

## How long to draw the lines representing the planets' orbits.
MAX_LINES = 3000

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
    global distScale
    return distScale * position

## Draws an arrow by drawing a line, picking two points either side of that line, and drawing lines from the end of the first line to those two points
def drawArrow(surface, colour, startPos, endPos):
    ## My solar system is in 3d space, but pygame can only handle 2d lines.
    ## The [:2] is necessary to deal with that.
    startPos, endPos = startPos[:2], endPos[:2]
    mainVector = (endPos - startPos)
    length = vec.mag(mainVector)
    pygame.draw.aaline(surface, colour, startPos, endPos)
    ## Generating the two points either side of the line
    normal = vec.normal(mainVector)
    point1 = startPos + 0.9*mainVector + 0.05*length*normal
    point2 = startPos + 0.9*mainVector - 0.05*length*normal
    pygame.draw.aaline(surface, colour, point1, endPos)
    pygame.draw.aaline(surface, colour, point2, endPos)

def displayArrows(planets, adjustment, focus, comFocus, surface):
    global distScale
    ## If no planet is being focused on then there's no arrows to draw
    if not comFocus:
        p = planets[focus]
        for arrow in p.getArrows():
            drawArrow(surface, arrow[0], p.getScaledPos()[:2]+adjustment, p.getScaledPos()[:2]+2*10**-12*distScale*arrow[1][:2]/(maths.log(p.getMass()))+adjustment)

def displayLines(planets, adjustment, focus, comFocus, surface):
    for p in planets:
        index = -1
        orbitalPath = [i[:2]+adjustment for i in scaledPos(np.array(p.getRecords()))]
        # lines = [[orbitalPath[i], orbitalPath[i+1]] for i in range(len(orbitalPath)-1)]
        for i in range(len(orbitalPath)-1):
            line = [orbitalPath[i], orbitalPath[i+1]]
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
            pygame.draw.aaline(surface,([int(indexRatio*colour) for colour in p.getColour()]),line[0],line[1],True)
        
def drawPlanet(p, position, surface):
    global distScale
    scaledSize = p.getSize()*distScale
    ## If the planet would fill the whole screen, there's no point trying to draw
    ## more of the circle than necessary, just fill the screen.
    ## This avoids severe lag when zooming in very closely.
    if scaledSize > vec.mag(centre):
        surface.fill(p.getColour())
    else:
        pygame.draw.circle(surface,p.getColour(),position,scaledSize)

    
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

def displayAttributeInfo(font, changingAttributes, properties, horizontalPos, surface):
    ## This is absolutely horrible code but it was the best way I could figure out of doing it

    ## The reason I have multiple textSurfaces is because pygame does not seem to support the "\n" character,
    ## so this is the only way I could get new lines.
    pygame.draw.rect(surface, 'black', (0, 0, 400, 150))
    if changingAttributes:
        text1 = "PRESS 'A' TO STOP EDITING ATTRIBUTES"
        text2 = "PRESS 'W' TO INCREASE VALUE OF G"
        text3 = "PRESS 'S' TO DECREASE VALUE OF G"
        text4 = "PRESS 'E' TO INCREASE PLANET'S MASS"
        text5 = "PRESS 'D' TO DECREASE PLANET'S MASS"
        text6 = "G: " + f'{G} Nm²/kg²'
    else:
        text1 = "PRESS 'A' TO EDIT G & PLANET MASS"
        text2 = "GPE: " + f'{properties[0]:.2e} J'
        text3 = "KE: " + f'{properties[1]:.2e} J'
        text4 = "TOTAL ENERGY: " + f'{properties[0]+properties[1]:.2e} J'
        text5 = "TOTAL MOMENTUM: " + f'{vec.mag(properties[2]):.2e} Ns'
        text6 = "G: " + f'{G} Nm²/kg²'
    textSurface1 = font.render(text1, True, (0, 255, 255))
    textSurface2 = font.render(text2, True, (0, 255, 255))
    textSurface3 = font.render(text3, True, (0, 255, 255))
    textSurface4 = font.render(text4, True, (0, 255, 255))
    textSurface5 = font.render(text5, True, (0, 255, 255))
    textSurface6 = font.render(text6, True, (0, 255, 255))
    screen.blit(surface, (horizontalPos-20, 0))
    screen.blit(textSurface1, (horizontalPos, 10))
    screen.blit(textSurface2, (horizontalPos, 30))
    screen.blit(textSurface3, (horizontalPos, 50))
    screen.blit(textSurface4, (horizontalPos, 70))
    screen.blit(textSurface5, (horizontalPos, 90))
    screen.blit(textSurface6, (horizontalPos, 110))

## This displays information on the desired planet.
def displayPlanetInfo(font, targetPlanet, planets, horizontalPos, surface):
    pygame.draw.rect(surface, 'black', (0, 0, 350, 125))
    text5 = "OBJECT: " + f'{targetPlanet.getName()}'
    text6 = "MASS: " + f'{targetPlanet.getMass():.2e} kg'
    text7 = "RADIUS: " + f'{targetPlanet.getSize()/1000:.2e} km'
    text8 = "DISTANCE FROM SUN: " + f'{vec.mag(targetPlanet.getPos()-planets[0].getPos())/1000:.2e} km'
    textSurface5 = font.render(text5, True, (0, 255, 255))
    textSurface6 = font.render(text6, True, (0, 255, 255))
    textSurface7 = font.render(text7, True, (0, 255, 255))
    textSurface8 = font.render(text8, True, (0, 255, 255))
    screen.blit(surface, (horizontalPos-20, 00))
    screen.blit(textSurface5, (horizontalPos, 10))
    screen.blit(textSurface6, (horizontalPos, 30))
    screen.blit(textSurface7, (horizontalPos, 50))
    screen.blit(textSurface8, (horizontalPos, 70))

def displayStartScreen(font):
    text1 = "Press the left and right arrow keys to switch between planets"
    text2 = "Press the up and down arrow keys to speed up and slow down time"
    text3 = "Press the space key to switch the focus to the centre of mass of the solar system"
    text4 = "Press 'F' to show the forces acting on the selected planet"
    text5 = "Press 'C' to enter comparison mode to compare sizes of planets"
    text6 = "Press 'A' to edit the strength of gravity (G) and the mass of planets"
    text7 = "Press Enter to start the program!"
    startScreenSurface1 = font.render(text1, True, (0, 255, 255))
    startScreenSurface2 = font.render(text2, True, (0, 255, 255))
    startScreenSurface3 = font.render(text3, True, (0, 255, 255))
    startScreenSurface4 = font.render(text4, True, (0, 255, 255))
    startScreenSurface5 = font.render(text5, True, (0, 255, 255))
    startScreenSurface6 = font.render(text6, True, (0, 255, 255))
    startScreenSurface7 = font.render(text7, True, (255, 0, 0))

    ## Display the start messages at equally spaced intervals down the screen.
    screen.blit(startScreenSurface1, (500, 1/7 * 0.9*centre[y]*2))
    screen.blit(startScreenSurface2, (500, 2/7 * 0.9*centre[y]*2))
    screen.blit(startScreenSurface3, (500, 3/7 * 0.9*centre[y]*2))
    screen.blit(startScreenSurface4, (500, 4/7 * 0.9*centre[y]*2))
    screen.blit(startScreenSurface5, (500, 5/7 * 0.9*centre[y]*2))
    screen.blit(startScreenSurface6, (500, 6/7 * 0.9*centre[y]*2))
    screen.blit(startScreenSurface7, (500, 7/7 * 0.9*centre[y]*2))

    pygame.display.flip()

## Finds the centre of mass of the system
def com(planets):
    positionMassSum = np.array([0.0,0.0,0.0])
    massSum = 0
    for p in planets:
        positionMassSum += p.getMass()*p.getPos()
        massSum += p.getMass()
    return positionMassSum/massSum

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

        p1.secondLaw()
        ## Uses verlet integration to update velocity and acceleration of planet
        p1.verlet(timeScale)
        ## Add a record of the planet's position so we can draw orbital lines.
        p1.addRecord(np.copy(p1.getPos()))
        ## Reset the resultant to 0 so it can be calculated again next tick
        p1.addForce(-p1.getResultant())

## Takes in vector, returns False if within the screen, True otherwise
def offscreen(vector):
    if vector[x] < 0 or vector[x] > centre[x]*2 or vector[y] < 0 or vector[y] > centre[y]*2:
        return True
    return False

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
        if len(self.__arrows) > len(planets):
            self.__arrows = self.__arrows[len(self.__arrows)-len(planets):]

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
        hostPos = self.getHost().getPos()
        updatedRecords = [i+hostPos for i in self.__records]
        return updatedRecords

    ## hostLine is the line drawn for the host on the current tick.
    ## Subtracting this from the line for our satellite "removes" the movement of the host.
    ## This leaves only the movement of the satellite around the host.
    def addRecord(self, record):
        hostPos = self.getHost().getPos()
        record = record - hostPos
        self.__records.append(record)
        if len(self.__records) > LINE_LENGTH:
            self.__records = self.__records[len(self.__records)-LINE_LENGTH:]

def generateSolarSystem():
    ## This list contains the name, NASA ID and colour of all the planets
    planets = []

    planetNames = ["Sun", "Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]
    planetColours = [(255, 255, 0), (65, 68, 74), (139, 115, 85), (0, 0, 255), (255, 99, 47), (250, 164, 87), (195, 146, 79), (98, 174, 230), (67, 109, 252), (204, 168, 132)]
    ## I do not want to add all 100+ moons of Jupiter, Saturn, Uranus and Neptune, hence only the important ones, our moon and the Galilean moons, are added
    moonNames = ["Moon", "Io", "Europa", "Ganymede", "Callisto"]
    moonColours = [(111, 109, 114), (253, 245, 144), (68, 169, 241), (92, 88, 76), (70, 103, 97)]
    ephemeris = horizonsParser.getEphemeris(10) ## Adding the sun
    planets.append(planet(planetNames[0], ephemeris[0], ephemeris[1], ephemeris[2], ephemeris[3], planetColours[0]))
    for i in range(1, 10):
        ephemeris = horizonsParser.getEphemeris(i*100+99)
        ## This is adding the moon, it makes sense for it to be just after earth in the planet order
        if i == 4:
            moonEphemeris = horizonsParser.getEphemeris(301)
            planets.append(satellite(moonNames[0], moonEphemeris[0], moonEphemeris[1], moonEphemeris[2], moonEphemeris[3], moonColours[0], planets[3]))
        ## For some reason, Jupiter's mass is given in grams by NASA
        ## Despite all other masses being given in kilograms
        ## I do not know why
        ## Dividing ephemeris[1] by 1000 resolves that problem
        ## Here we also add the planets Europa, Io, Ganymede and Callisto (this is done at i=6 so that they are AFTER jupiter in the list)
        ## Their IDs follow the pattern 501, 502, 503 etc so 500+j is used to generate them
        if i == 5:
            ephemeris[1] = ephemeris[1]/1000
        if i == 6:
            for j in range(1,5):
                moonEphemeris = horizonsParser.getEphemeris(500+j, True)
                planets.append(satellite(moonNames[j], moonEphemeris[0], moonEphemeris[1], moonEphemeris[2], moonEphemeris[3], moonColours[j], planets[6]))

        planets.append(planet(planetNames[i], ephemeris[0], ephemeris[1], ephemeris[2], ephemeris[3], planetColours[i]))
    # Adding a few prominent satellites (voyager 1&2)
    ephemeris=horizonsParser.getEphemeris(-31, False, True, 722, 13) # Voyager 1, need to manually input mass and size as NASA does not provide it
    planets.append(planet("Voyager 1", ephemeris[0], ephemeris[1], ephemeris[2], ephemeris[3], moonColours[0])) ## moonColours[0] is grey, spacecraft are grey, close enough
    ephemeris=horizonsParser.getEphemeris(-32, False, True, 722, 13) # Voyager 2
    planets.append(planet("Voyager 2", ephemeris[0], ephemeris[1], ephemeris[2], ephemeris[3], moonColours[0]))
    return planets

planets = generateSolarSystem()

## The -3 here is because of the moons, voyager 1 and 2, which are not usually visible and so will not cause extra lag from their orbital paths
LINE_LENGTH = int(MAX_LINES / (len(planets)-7))
pygame.init()
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
## Centre is never edited and is needed by lots of functions so makes sense to have it as global
centre = np.array(pygame.display.get_surface().get_size())/2

def main():
    global distScale
    global zoomScale
    global G
    framerate = 120
    ## Time-scale, how much vel and position should change per tick
    ## Lower value = slower but more accurate simulation
    year = 31536000/framerate
    timeScale = 0.05*year

    ## Centre of screen
    clock = pygame.time.Clock()
    started = False
    running = True
    arrowsToDraw = []
    focus = 0
    comFocus = False
    arrows = False
    comparison = False
    changingAttributes = False
    planetsToCompare = [0, 6]
    comparisonSurface1 = pygame.Surface((centre[x]-3, centre[y]*2))
    comparisonSurface2 = pygame.Surface((centre[x]-3, centre[y]*2))
    font = pygame.font.SysFont('codenewroman', 18)
    bigFont = pygame.font.SysFont('codenewroman', 22)
    ## Menu surface 1 is for displaying the energies
    menuSurface1 = pygame.Surface((400, 200), pygame.SRCALPHA)
    ## Menu surface 2 is for displaying planet info
    menuSurface2 = pygame.Surface((400, 200), pygame.SRCALPHA)
    menuSurface1.set_alpha(128)
    menuSurface2.set_alpha(128)
    ## Display a start screen that also explains all the keybinds
    while not started:
        screen.fill((0,0,0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    started = True

        displayStartScreen(bigFont)

    while running:
        screen.fill((0,0,0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    if comparison:
                        planetsToCompare[1] = (planetsToCompare[1]+1) % len(planets)
                    else:
                        focus = (focus+1)%len(planets)
                elif event.key == pygame.K_LEFT:
                    if comparison:
                        planetsToCompare[0] = (planetsToCompare[0]+1) % len(planets)
                    else:
                        focus = (focus-1)%len(planets)
                elif event.key == pygame.K_UP:
                    if timeScale == 0:
                        timeScale = 0.05*year
                    else:
                        timeScale += 0.1*year
                elif event.key == pygame.K_DOWN:
                    timeScale -= 0.1*year
                    ## Don't want negative time
                    if timeScale < 0:
                        timeScale = 0
                elif event.key == pygame.K_SPACE:
                    ## Toggles whether or not the screen is centered on the centre of mass
                    comFocus = not comFocus
                elif event.key == pygame.K_f:
                    arrows = not arrows
                elif event.key == pygame.K_c:
                    comparison = not comparison
                elif event.key == pygame.K_a:
                    changingAttributes = not changingAttributes
                ## G is very small, but users might want very large values of G.
                ## To achieve this, I make the increments G go up in scale with the order of magnitude of G.
                ## The same thing is done with masses of planets, as a very different increment is needed
                ## for something the size of a satellite compared to something the size of our sun
                elif event.key == pygame.K_w:
                    if changingAttributes:
                        G += 0.5*10**maths.floor((maths.log(G, 10)))
                elif event.key == pygame.K_s:
                    if changingAttributes:
                        G -= 0.5*10**maths.floor((maths.log(G, 10)))
                elif event.key == pygame.K_e:
                    if changingAttributes:
                        oldMass = planets[focus].getMass()
                        if not comFocus:
                            planets[focus].addMass(0.5*10**maths.floor(maths.log(planets[focus].getMass()+1,10)))
                elif event.key == pygame.K_d:
                    if changingAttributes:
                        if not comFocus:
                            planets[focus].addMass(-0.5*10**maths.floor(maths.log(planets[focus].getMass()+1,10)))
                            
                
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
            pygame.draw.rect(comparisonSurface1, 'black', (0, 0, centre[x]*2, centre[y]*2))
            pygame.draw.rect(comparisonSurface2, 'black', (0, 0, centre[x]*2, centre[y]*2))
            drawPlanet(planets[planetsToCompare[0]], np.array([centre[x]/2, centre[y]]), comparisonSurface1)
            drawPlanet(planets[planetsToCompare[1]], np.array([centre[x]/2, centre[y]]), comparisonSurface2)
            screen.blit(comparisonSurface1, (0, 0))
            screen.blit(comparisonSurface2, (centre[x]+3, 0))
            pygame.draw.line(screen, "blue", [centre[x],0], [centre[x],centre[y]*2], 6)
            ## Display info on both selected planets
            displayPlanetInfo(font, planets[planetsToCompare[0]], planets, 20, menuSurface2)
            displayPlanetInfo(font, planets[planetsToCompare[1]], planets, centre[x]*2-280, menuSurface2)

        else:
            adjustment = focusAdjustment(planets, focus, comFocus)
            displayPlanets(planets, adjustment, screen)
            displayLines(planets, adjustment, focus, comFocus, screen)
            if arrows:
                displayArrows(planets, adjustment, focus, comFocus, screen)

            ## Properties includes the key physical attributes of the system, potential energy, kinetic energy, momenteum
            properties = sumPhysicalProperties(planets)
            ## Displaying the menu
            displayAttributeInfo(font, changingAttributes, properties, 20, menuSurface1)
            ## Display info on current planet as requested by client
            if not comFocus:
                displayPlanetInfo(font, planets[focus], planets, centre[x]*2-280, menuSurface2)

        pygame.display.flip()
        clock.tick(framerate)
main()