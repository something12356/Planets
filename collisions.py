import pygame
import random
import numpy as np

SIZE = [1920, 1080]
T = 0.1

x = 0
y = 1

class ball:
    def __init__(self,pos,vel,size,colour):
        self.pos = pos
        self.vel = vel
        self.size = size
        self.colour = colour
        self.isColliding = False

    def move(self):
        self.pos += T*self.vel

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

balls = [ball(np.array([random.uniform(50,SIZE[x]-50),random.uniform(50,SIZE[y]-50)]),np.array([random.uniform(-20,20),random.uniform(-20,20)]),random.randint(10,50),(random.randint(0,255),random.randint(0,255),random.randint(0,255))) for i in range(5)]

pygame.init()
screen = pygame.display.set_mode((SIZE[x],SIZE[y]))
clock = pygame.time.Clock()
running = True
while True:
    screen.fill(0)
    for ball in balls:
        pygame.draw.circle(screen,ball.colour,ball.pos,ball.size)
        ball.move()
        ball.reflect()
        for ball2 in balls:
            if ball2 == ball or ball2.isColliding:
                continue
            if abs(ball2.pos[x] - ball.pos[x]) < ball.size+ball2.size and abs(ball2.pos[y] - ball.pos[y]) < ball.size+ball2.size:
                ball.collide(ball2)
                ball.isColliding = True
                ball2.isCollidng = True
    for ball in balls:
        ball.isColliding = False

    pygame.display.flip()
    clock.tick(1/T*30)