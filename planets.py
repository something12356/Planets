import math as maths
import pygame_sdl2 as pygame
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
    
    ## Uses F = GMm/r**2 to work out the force on a planet
    ## Breaks it into components by doing F*adj/hyp, F*opp/hyp (Fcos(a) and Fsin(a))
    def gravity(self, planet2):
        r = planet2.pos - self.pos
        F = G*(self.mass*planet2.mass)/(mag(r)**2)
        Fx = F*r[0]/mag(r)
        Fy = F*r[1]/mag(r)
        return np.array([Fx,Fy])
    
    ## Uses F = ma to find acceleration, add to velocity
    def secondLaw(self, F):
        self.velocity += T*F/self.mass
    
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

sun = planet(20,np.array([0.0,0.0]),1000000,np.array([960.0,540.0]),(255,255,0))
venus = planet(7,np.array([-2.0,1.0]),1,np.array([1200.0,910.1]),(139,115,85))
earth = planet(7,np.array([4.0,-1.0]),1,np.array([960.0,270.0]),(0,0,255))
# moon = planet(5,np.array([2.8690832,-0.03653574]),0.012,np.array([955.0,270]),"grey")
jupiter = planet(10,np.array([0.0,2.0]),333,np.array([500.0,540.0]),(210,105,30))
planets = [sun,venus,earth,jupiter]

pygame.init()
screen = pygame.display.set_mode((1920,1080))
clock = pygame.time.Clock()
running = True
count = 0
linesToDraw = []
focus = 0
comFocus = True

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
        pygame.draw.aaline(screen,([indexRatio*line[2][i] for i in range(3)]),line[0],line[1],indexRatio*255)
        index+=1
    ## Gets rid of excess lines, prevents them from becoming too long
    if len(linesToDraw) > LINE_LENGTH:
        linesToDraw = linesToDraw[len(linesToDraw)-LINE_LENGTH:]

    ## Works out gravitational force between all planets and moves them according each tick
    for p1 in planets:
        F = 0
        for p2 in planets:
            if p1 == p2:
                continue
            F += p1.gravity(p2)
        p1.secondLaw(F)
        ## Takes position before and after so that the lines for the orbits can be drawn
        beforePos = np.copy(p1.pos)
        p1.move()
        afterPos = np.copy(p1.pos)
        linesToDraw.append([beforePos,afterPos,p1.colour])
        pygame.draw.circle(screen,p1.colour,p1.pos,p1.size)
        pygame.draw.aaline(screen,(p1.colour),p1.pos,p1.pos)

    pygame.display.flip()
    clock.tick(60)