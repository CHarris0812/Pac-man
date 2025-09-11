import pygame

from boardUtils import findTile, findCenter

class Character():
    def __init__(self, name, startPos, size, speed, color, tileSize):
        self.name = name
        self.size = size
        self.speed = speed
        self.direction = "left"
        self.sprite = pygame.Rect(0, 0, size, size)
        self.sprite.center = startPos
        self.tile = findTile(self.sprite.center, tileSize)
        self.newLocation = self.sprite.center
        self.startPos = startPos
        self.color = color
        self.tileSize = tileSize

    def draw(self, window, color):
        pygame.draw.rect(window, color, self.sprite)

    #Teleport either right or left. Return new tile as well as new center
    def teleport(self):
        if self.tile == (0, 17) and self.direction == "left": #Left teleport
            self.tile = (27, 17)
            self.sprite.center = findCenter(self.tile, self.tileSize)
        elif self.tile == (27, 17) and self.direction == "right": #Right teleport
            self.tile = (0, 17)
            self.sprite.center = findCenter(self.tile, self.tileSize)