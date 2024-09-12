import math as maths
import numpy as np
import vectors as vec

## Gravitational constant, defines how strong gravity is.
G = 6.6743015*10**-11
x = 0
y = 1

def simulateTick(arrowsToDraw, planets, timeScale, focus, comFocus):
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
        p1.verletPosition(timeScale)
        afterPos = np.copy(p1.getPos())
        p1.addLine([beforePos,afterPos,p1.getColour()])  
        ## Reset the resultant to 0 so it can be calculated again next tick
        p1.addForce(-p1.getResultant())

    return arrowsToDraw

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
    def verletPosition(self, timeScale):
        self.__vel += self.getAccel()*timeScale
        self.__pos += self.getVel()*timeScale

    ## End of getters and setters

    ## Uses F = GMm/r**2 to work out the force on a planet
    ## Breaks it into components by doing F*adj/hyp, F*opp/hyp (Fcos(a) and Fsin(a))
    def gravity(self, planet2):
        r = planet2.getPos() - self.getPos()
        F = G*(self.getMass()*planet2.getMass())/(vec.mag(r)**2)
        Fx = F*r[x]/vec.mag(r)
        Fy = F*r[y]/vec.mag(r)
        return np.array([Fx,Fy])

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