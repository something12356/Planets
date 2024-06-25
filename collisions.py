import pygame
import random
import numpy as np
import math as maths

SIZE = [1920, 1080]
T = 0.1

x = 0
y = 1

def mag(vec):
    mag = 0
    for i in vec:
        mag += i**2
    return maths.sqrt(mag)

def unit(vec):
    if mag(vec) == 0:
        return vec
    return vec*(1/mag(vec))

def dot(vec1, vec2):
    if len(vec1) != len(vec2):
        return "Dimension error!"
    else:
        return sum([vec1[i]*vec2[i] for i in range(len(vec1))])

def addToCells(cells, balls):
    cells = [[] for i in range(5184)]
    for ball in balls:
        i = round(ball.pos[x])//20-1
        j = round(ball.pos[y])//20-1
        cells[j*96+i].append(ball)
    return cells

class ball:
    def __init__(self,pos,vel,size,colour):
        self.pos = pos
        self.vel = vel
        self.size = size
        self.colour = colour
        self.isColliding = False

    def move(self):
        newPos = self.pos + T*self.vel
        if newPos[x] >= self.size and newPos[x] <= SIZE[x]-self.size and newPos[y] >= self.size and newPos[y] <= SIZE[y]-self.size:
            self.pos = newPos
        else:
            newPos = self.pos
            while newPos[x] >= self.size and newPos[x] <= SIZE[x]-self.size and newPos[y] >= self.size and newPos[y] <= SIZE[y]-self.size:
                newPos += unit(self.vel)
            self.pos = newPos

    def reflect(self, e=1):
        for i in range(2):
            if self.pos[i] <= self.size or self.pos[i] >= SIZE[i] - self.size:
                self.vel[i] = -e*self.vel[i]

                if self.pos[i] < self.size:
                    self.pos[i] = self.size

                if self.pos[i] > SIZE[i] - self.size:
                    self.pos[i] = SIZE[i] - self.size

    def collide(self, ball2, e=1):
        n = unit(ball2.pos-self.pos)
        dot1 = dot(self.vel, n)
        dot2 = dot(ball2.vel, n)
        tan1,norm1, tan2,norm2 = self.vel - dot1*n,dot1, ball2.vel-dot2*n,dot2
        m1, m2 = self.size, ball2.size
        # print(m1*mag(self.vel)**2+m2*mag(ball2.vel)**2)
        norm1New, norm2New = (norm1*m1+norm2*m2-m2*e*(norm1-norm2))/(m1+m2), (norm1*m1+norm2*m2-m1*e*(norm2-norm1))/(m1+m2)
        self.vel = tan1+norm1New*n
        ball2.vel = tan1+norm2New*n
        # print(m1*mag(self.vel)**2+m2*mag(ball2.vel)**2)

balls = [ball(np.array([random.uniform(0.0,1920.0),random.uniform(0.0,1080.0)]),np.array([(-1)**i*random.uniform(0.0,40.0),(-1)**i*random.uniform(0.0,40.0)]),random.uniform(9,10),(i%255,0,255-i%255)) for i in range(256)]
# balls.append(ball(np.array([20.0,520.0]),np.array([0.0,0.0]),20,"blue"))
cells = []

pygame.init()
screen = pygame.display.set_mode((SIZE[x],SIZE[y]))
clock = pygame.time.Clock()
running = True
count = 0
while True:
    screen.fill(0)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                T += 0.01
            if event.key == pygame.K_DOWN:
                T -= 0.01
    # if count % 10 == 0:
    #     colOffset = count % 1020
    #     if colOffset > 510:
    #         colOffset = 1020 - colOffset
    #     print(colOffset)
    #     a = 255 - colOffset
    #     if a < 0:
    #         a = 0
    #     b = colOffset
    #     if b > 255:
    #         b = 510 - b
    #     c = colOffset - 255
    #     if c < 0:
    #         c = 0
    #     print(a,b,c)
    #     balls.append(ball(np.array([20.0,20.0]),np.array([1200.0,0.0]),10,(a,b,c)))

    cells = addToCells(cells, balls)

    for i in range(len(cells)):
        for ball1 in cells[i]:
            pygame.draw.circle(screen,ball1.colour,ball1.pos,ball1.size)
            ball1.move()        
            ball1.reflect(1.5)
            for j in [-97,-96,-95,-1,0,1,95,96,97]:
                if i+j > 5183 or i+j < 0:
                    continue
                for ball2 in cells[i+j]:
                    if ball2 == ball1:
                        continue
                    overlap = ball1.size+ball2.size - mag(ball1.pos-ball2.pos)
                    if overlap > 0:
                        ball1.pos += 0.5*overlap*unit(ball1.pos-ball2.pos)
                        ball2.pos += 0.5*overlap*unit(ball2.pos-ball1.pos)
                        if ball1.isColliding or ball2.isColliding:
                            continue
                        ball1.collide(ball2, 0)
                        ball1.isColliding = True
                        ball2.isColliding = True

    energy = 0
    for ball1 in balls:
        ball1.isColliding = False
        energy += 0.5*ball1.size*mag(ball1.vel)**2
        print(mag(ball1.vel))
    print("Total kinetic energy:",energy)
    count += 1
    # if count == 50:
    #     balls[-1].vel = np.array([200.0,0.0])
    print('---')
    pygame.display.flip()
    clock.tick(60)