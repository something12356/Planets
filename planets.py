import math as maths
import pygame
import numpy as np

## Time-scale, how much vel and position should change per tick
## Lower value = slower but more accurate simulation
T=1
## Gravitational constant, defines how strong gravity is
G = 6.6743015*10**-3

## How long to draw the lines representing the planets' orbits.
LINE_LENGTH = 1000

## Centre of screen
centre = np.array([960.0,540.0])

## Finds the magnitude of a vector (np array)
def mag(vec):
    mag = 0
    for i in vec:
        mag += i**2
    return maths.sqrt(mag)

## Returns a vector with the same direction as the input of length 1
def unit(vec):
    if mag(vec) == 0:
        return vec
    return vec*(1/mag(vec))

## Returns a direction vector (a vector of unit length 1 so it can easily be scaled) that is perpendicular to input line
## By taking the "negative reciprocal", swapping the values and multiplying one of them by -1
def normal(vector):
    normal = np.array([-1*vector[1],vector[0]])
    return unit(normal)

## Draws an arrow by drawing a line, picking two points either side of that line, and drawing lines from the end of the first line to those two points
def drawArrow(colour, startPos, endPos):
    vec = endPos - startPos
    length = mag(vec)
    pygame.draw.aaline(screen, colour, startPos, endPos)
    ## Generating the two points either side of the line
    norm = normal(vec)
    p1 = startPos + 0.8*vec + 0.15*length*norm
    p2 = startPos + 0.8*vec - 0.15*length*norm
    pygame.draw.aaline(screen, colour, p1, endPos)
    pygame.draw.aaline(screen, colour, p2, endPos)

## Finds the centre of mass of the sysetm
def com(planets):
    com = np.array([0.0,0.0])
    mass = 0
    for p in planets:
        com[0] += p.getMass()*p.getPos()[0]
        com[1] += p.getMass()*p.getPos()[1]
        mass += p.getMass()
    return com/mass

class planet:
    def __init__(self,size,vel,mass,pos,colour):
        self.size = size
        self.vel = vel
        self.mass = mass
        self.pos = pos
        self.colour = colour
        self.resultant = 0
    
    ## All the getters and setters
    def getPos(self):
        return self.pos

    def getMass(self):
        return self.mass

    def getVel(self):
        return self.vel

    def getResultant(self):
        return self.resultant

    def getColour(self):
        return self.colour

    def getSize(self):
        return self.size

    ## Adds a force to the resultant force on the planet
    def addForce(self, force):
        self.resultant += force

    ## Sets velocity
    ## Uses F = ma to find acceleration, add to vel
    def secondLaw(self, force):
        self.vel += T*force/self.getMass()
    
    ## Sets position
    ## Add vel to position to make it move
    def move(self, step):
        self.pos += step

    ## End of getters and setters

    ## Uses F = GMm/r**2 to work out the force on a planet
    ## Breaks it into components by doing F*adj/hyp, F*opp/hyp (Fcos(a) and Fsin(a))
    def gravity(self, planet2):
        r = planet2.getPos() - self.getPos()
        F = G*(self.getMass()*planet2.getMass())/(mag(r)**2)
        Fx = F*r[0]/mag(r)
        Fy = F*r[1]/mag(r)
        return np.array([Fx,Fy])

## All the planets being defined
# sun1 = planet(30,np.array([0.0,0.0]),4000,np.array([960.0,780.0]),(0,255,255))
# sun2 = planet(30,np.array([0.0,0.0]),4000,np.array([960.0,300.0]),(0,255,255))
# # sun3 = planet(30,np.array([0.0,0.0]),4000,np.array([1800.0,540.0]),"red")
# # sun4 = planet(30,np.array([0.0,0.0]),4000,np.array([120.0,540.0]),"red")
# earth = planet(5,np.array([0.3,0.0]),1,np.array([960.0,50.0]),(0,0,255))
# planets = [sun1,sun2,earth]

sun = planet(20,np.array([1.0,0.0]),1000000,np.array([960.0,540.0]),(255,255,0))
venus = planet(7,np.array([-2.0,-1.0]),1,np.array([1200.0,910.1]),(139,115,85))
earth = planet(7,np.array([5.0,-2.0]),1,np.array([960.0,270.0]),(0,0,255))
# moon = planet(5,np.array([2.8690832,-0.03653574]),0.012,np.array([955.0,270]),"grey")
jupiter = planet(10,np.array([0.0,3.0]),33300,np.array([500.0,540.0]),(210,105,30))
planets = [sun,venus, earth, jupiter]

pygame.init()
screen = pygame.display.set_mode((1920,1080))
clock = pygame.time.Clock()
running = True
count = 0
linesToDraw = []
arrowsToDraw = []
focus = 0
comFocus = True
arrows = False

while running:
    screen.fill((0,0,0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                focus = (focus+1)%len(planets)
            if event.key == pygame.K_LEFT:
                focus = (focus-1)%len(planets)
            if event.key == pygame.K_UP:
                T += 0.1
            if event.key == pygame.K_DOWN:
                T -= 0.1
            if event.key == pygame.K_SPACE:
                ## Toggles whether or not the screen is centered on the centre of mass
                comFocus = not comFocus
            if event.key == pygame.K_f:
                arrows = not arrows

    ## Works out gravitational force between all planets and moves them according each tick
    for p1 in planets:
        for p2 in planets[planets.index(p1)+1:]:
            p1p2gravity = p1.gravity(p2)
            strength = mag(p1p2gravity)
            p1.addForce(p1p2gravity)
            ## Draws force arrows showing the forces acting on the planet
            if planets.index(p1) == focus and not comFocus:
                arrowsToDraw.append(["white", p1.getPos(), np.copy(p1p2gravity), p1.getSize()])
            if planets.index(p2) == focus and not comFocus:
                arrowsToDraw.append(["white", p2.getPos(), -1*np.copy(p1p2gravity), p2.getSize()])
            ## Can take away here due to Newton's third law, each force has equal and opposite reaction force
            p2.addForce(-p1p2gravity)
        if planets.index(p1) == focus and not comFocus:
            arrowsToDraw.append([p1.getColour(), p1.getPos(), np.copy(p1.getResultant()), p1.getSize()])
            arrowsToDraw.append(np.copy(p1.getResultant()))
        p1.secondLaw(p1.getResultant())
        ## Takes position before and after so that the lines for the orbits can be drawn
        beforePos = np.copy(p1.getPos())
        p1.move(T*p1.getVel())
        afterPos = np.copy(p1.getPos())
        linesToDraw.append([beforePos,afterPos,p1.getColour()])
        p1.resultant = 0

        ## Makes it so that the screen follows whichever planet the user wants to look at
    ## Alternatively follows the centre of mass, useful for binary star systems
    if comFocus:
        focusDisplacement = centre - com(planets)
    else:
        focusDisplacement = centre - planets[focus].getPos()
    for p in planets:
        p.move(focusDisplacement)
    for line in linesToDraw:
        line[0] += focusDisplacement
        line[1] += focusDisplacement

    index = 0
    for line in linesToDraw:
        ## Index ratio is used to reduce opacity and thickness of the older lines 
        ## An index counter is used as python cannot find the index of np arrays with multiple elements
        indexRatio = index/len(linesToDraw)
        pygame.draw.aaline(screen,([int(indexRatio*line[2][i]) for i in range(3)]),line[0],line[1],int(indexRatio*255))
        index+=1
    ## Gets rid of excess lines, prevents them from becoming too long and lagging the system
    if len(linesToDraw) > LINE_LENGTH:
        linesToDraw = linesToDraw[len(linesToDraw)-LINE_LENGTH:]

    if not arrows:
        arrowsToDraw = []
    else:
        if len(arrowsToDraw) > 0:
            forceToDraw = arrowsToDraw[-1]
    while len(arrowsToDraw) > 1:
        arrow = arrowsToDraw.pop(0)
        if arrow[0] != "white":
            # print("RESULTANT:", abs(maths.log(mag(forceToDraw)+1,1000))*240*mag(arrow[2]), abs(arrow[3]))
            drawArrow(arrow[0], arrow[1], arrow[1]+abs(maths.log(mag(forceToDraw)+1,1000))*240*mag(arrow[2])/mag(forceToDraw)*unit(arrow[2])+(arrow[3]+20)*unit(arrow[2]))
        else:
            # print("COMPONENT:", abs(maths.log(mag(forceToDraw)+1,1000))*240*mag(arrow[2]), abs(arrow[3]))
            drawArrow(arrow[0], arrow[1], arrow[1]+abs(maths.log(mag(forceToDraw)+1,1000))*60*mag(arrow[2])/mag(forceToDraw)*unit(arrow[2])+(arrow[3]+10)*unit(arrow[2]))
    arrowsToDraw = []

    ## Draws all the planets
    for p in planets:       
        pygame.draw.circle(screen,p.getColour(),p.getPos(),p.getSize())
        pygame.draw.aaline(screen,(p.getColour()),p.getPos(),p.getPos())

    pygame.display.flip()
    clock.tick(60)