import pygame as pg
import random

# Настройки окна
WIDTH = 300
HEIGHT = 500

# Палитра
WHITE = (255, 255, 255)
RED = (241, 58, 19)
BLACK = (0, 0, 0)

SPEED = 2
# Машинка №1
CAR_WIDTH = 40
CAR_HEIGHT = 70
xpos = 130
ypos = 405
car = WrappedRect(RED, xpos, ypos, CAR_WIDTH, CAR_HEIGHT)

# Машинка №2
y_enemy = 0 - CAR_HEIGHT
x_enemy = random.choice([10, 130, 250])
car_enemy = WrappedRect(BLACK, x_enemy, y_enemy, CAR_WIDTH, CAR_HEIGHT)

def events(e):
    if e.type == pg.KEYDOWN:
        if e.key == pg.K_LEFT and car.x > 10:
                car.x -= 60
        if e.key == pg.K_RIGHT and car.x < 250:
                car.x += 60

def updates():
    global running, SPEED
    if car_enemy.y >= HEIGHT + CAR_HEIGHT:
        SPEED += 0.7
        car_enemy.y = 0 - CAR_HEIGHT
        car_enemy.x = random.choice([10, 130, 250])
    else:
        car_enemy.y += SPEED  # Прибавление скорости
    
    # Обработка столкновения
    if car.colliderect(car_enemy):
        running = False

def draw(screen):
    screen.fill(WHITE)
    car.draw(screen)
    car_enemy.draw(screen)

