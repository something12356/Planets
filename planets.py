import math as maths
import pygame
import numpy as np

## Time-scale, how much velocity and position should change per tick
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
        com[0] += p.mass*p.pos[0]
        com[1] += p.mass*p.pos[1]
        mass += p.mass
    return com/mass

class planet:
    def __init__(self,size,velocity,mass,pos,colour):
        self.size = size
        self.velocity = velocity
        self.mass = mass
        self.pos = pos
        self.colour = colour
        self.checked = False
        self.force = 0
    
    ## Uses F = GMm/r**2 to work out the force on a planet
    ## Breaks it into components by doing F*adj/hyp, F*opp/hyp (Fcos(a) and Fsin(a))
    def gravity(self, planet2):
        r = planet2.pos - self.pos
        F = G*(self.mass*planet2.mass)/(mag(r)**2)
        Fx = F*r[0]/mag(r)
        Fy = F*r[1]/mag(r)
        return np.array([Fx,Fy])
    
    ## Uses F = ma to find acceleration, add to velocity
    def secondLaw(self):
        self.velocity += T*self.force/self.mass
    
    ## Add velocity to position to make it move
    def move(self):
        self.pos += T*self.velocity

## All the planets being defined
# sun1 = planet(30,np.array([0.0,0.0]),4000,np.array([960.0,780.0]),(0,255,255))
# sun2 = planet(30,np.array([0.0,0.0]),4000,np.array([960.0,300.0]),(0,255,255))
# # sun3 = planet(30,np.array([0.0,0.0]),4000,np.array([1800.0,540.0]),"red")
# # sun4 = planet(30,np.array([0.0,0.0]),4000,np.array([120.0,540.0]),"red")
# earth = planet(5,np.array([0.3,0.0]),1,np.array([960.0,50.0]),(0,0,255))
# planets = [sun1,sun2,earth]

sun = planet(20,np.array([1.0,0.0]),1000000,np.array([960.0,540.0]),(255,255,0))
venus = planet(7,np.array([-2.0,1.0]),1,np.array([1200.0,910.1]),(139,115,85))
earth = planet(7,np.array([4.0,-1.0]),1,np.array([960.0,270.0]),(0,0,255))
# moon = planet(5,np.array([2.8690832,-0.03653574]),0.012,np.array([955.0,270]),"grey")
jupiter = planet(10,np.array([0.0,2.0]),333,np.array([500.0,540.0]),(210,105,30))
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

    ## Makes it so that the screen follows whichever planet the user wants to look at
    ## Alternatively follows the centre of mass, useful for binary star systems
    if comFocus:
        focusDisplacement = centre - com(planets)
    else:
        focusDisplacement = centre - planets[focus].pos
    for p in planets:
        p.pos += focusDisplacement
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
    while len(arrowsToDraw) > 0:
        arrow = arrowsToDraw.pop()
        print(unit(arrow[2]))
        force = arrow[3]
        scalar = 40
        if arrow[0] != "white":
            scalar = 80
        drawArrow(arrow[0], arrow[1], arrow[1]+scalar*mag(arrow[2])/mag(force)*unit(arrow[2])+(scalar/2)*unit(arrow[2]))

    ## Works out gravitational force between all planets and moves them according each tick
    for p1 in planets:
        for p2 in planets[planets.index(p1)+1:]:
            p1p2gravity = p1.gravity(p2)
            strength = mag(p1p2gravity)
            p1.force += p1p2gravity
            ## Draws force arrows showing the forces acting on the planet
            if planets.index(p1) == focus and not comFocus:
                arrowsToDraw.append(["white", p1.pos, np.copy(p1p2gravity), np.copy(p1.force)])
            if planets.index(p2) == focus and not comFocus:
                arrowsToDraw.append(["white", p2.pos, -1*np.copy(p1p2gravity), np.copy(p1.force)])
            ## Can take away here due to Newton's third law, each force has equal and opposite reaction force
            p2.force -= p1p2gravity
        if planets.index(p1) == focus and not comFocus:
            arrowsToDraw.append([p1.colour, p1.pos, np.copy(p1.force), np.copy(p1.force)])
        p1.secondLaw()
        ## Takes position before and after so that the lines for the orbits can be drawn
        beforePos = np.copy(p1.pos)
        p1.move()
        afterPos = np.copy(p1.pos)
        linesToDraw.append([beforePos,afterPos,p1.colour])
        pygame.draw.circle(screen,p1.colour,p1.pos,p1.size)
        pygame.draw.aaline(screen,(p1.colour),p1.pos,p1.pos)
        p1.force = 0

    pygame.display.flip()
    clock.tick(60)