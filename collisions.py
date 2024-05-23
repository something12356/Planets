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

    def reflect(self):
        for i in range(2):
            if self.pos[i] <= self.size or self.pos[i] >= SIZE[i] - self.size:
                self.vel[i] = -self.vel[i]

                if self.pos[i] < self.size:
                    self.pos[i] = self.size

                if self.pos[i] > SIZE[i] - self.size:
                    self.pos[i] = SIZE[i] - self.size

    
    def collide(self,ball2):
        m1, m2 = self.size, ball2.size
        a,b, c,d = self.vel[x],self.vel[y], ball2.vel[x],ball2.vel[y]
        self.vel[x], ball2.vel[x] = (m1*a-m2*a+2*m2*c)/(m1+m2), (m2*c-m1*c+2*m1*a)/(m1+m2)
        self.vel[y], ball2.vel[y] = (m1*b-m2*b+2*m2*d)/(m1+m2), (m2*d-m1*d+2*m1*b)/(m1+m2)

balls = [ball(np.array([960.0,540.0]),np.array([random.choice([-0.000000001,0.0000000001])*random.uniform(5000.0,10000.0),random.choice([-0.000000001,0.000000001])*random.uniform(5000.0,10000.0)]),random.uniform(10,20),(random.randint(0,255),random.randint(0,255),random.randint(0,255))) for i in range(400)]
balls.append(ball(np.array([20.0,540.0]),np.array([0.0,0.0]),50,"blue"))

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

    for ball in balls:
        pygame.draw.circle(screen,ball.colour,ball.pos,ball.size)
        ball.move()
        ball.reflect()

    for ball in balls:
        for ball2 in balls[balls.index(ball)+1:]:
            overlap = ball.size+ball2.size - mag(ball.pos-ball2.pos)
            if ball2 == ball or ball.isColliding or ball2.isColliding:
                continue
            
            if overlap > 0:
                ball.pos += overlap*unit(ball.pos-ball2.pos)
                ball2.pos += overlap*unit(ball2.pos-ball.pos)
                if mag(ball.pos-ball2.pos) == 0:
                    ball.pos += overlap*np.array([random.uniform(-1,1),random.uniform(-1,1)])
                    ball2.pos += overlap*np.array([random.uniform(-1,1),random.uniform(-1,1)])
                ball.collide(ball2)
                ball.isColliding = True
                ball2.isColliding = True

    energy = 0
    for ball in balls:
        ball.isColliding = False
        energy += 0.5*ball.size*(mag(ball.vel)**2)
        if mag(ball.vel) != 0:
            print(mag(ball.vel))
    print("Total kinetic energy:",energy)
    count += 1
    if count == 400:
        balls[-1].vel = np.array([1000.0,1000.0])

    print('---')
    pygame.display.flip()
    clock.tick(60)