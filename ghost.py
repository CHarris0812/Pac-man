import pygame

from boardUtils import findTile
from character import Character

class Ghost(Character):
    def __init__(self, name, startPos, scatterTile, size, speed, releaseLocation, releaseCounter, releaseThreshold, color, tileSize):
        super().__init__(name, startPos, size, speed, color, tileSize)
        self.scatterTile = scatterTile
        self.target = scatterTile
        self.released = False
        self.eaten = False
        self.releaseLocation = releaseLocation
        self.released = False
        self.releaseCounter = releaseCounter
        self.releaseThreshold = releaseThreshold

    def update_tile(self):
        pass

    def chooseTarget(self, chaseMode, pacmanTile, blinkyTile):
        if not chaseMode: return self.scatterTile
        elif self.name == "pinky": return self.pinkyTarget(pacmanTile)
        elif self.name == "inky": return self.inkyTarget(pacmanTile, blinkyTile)
        elif self.name == "clyde": return self.clydeTarget(pacmanTile)
        else: return self.blinkyTarget(pacmanTile)

    def pinkyTarget(self, pacmanTile):
        if self.direction == "left":
            return (max(0, pacmanTile[0] - 4), pacmanTile[1])
        elif self.direction == "right":
            return (min(27, pacmanTile[0] + 4), pacmanTile[1])
        elif self.direction == "up":
            return (pacmanTile[0], max(0, pacmanTile[1] - 4))
        else:
            return (pacmanTile[0], min(35, pacmanTile[1] + 4))

    def inkyTarget(self, pacmanTile, blinkyTile):
        tempTarget = self.pinkyTarget(pacmanTile)

        xDistance = blinkyTile[0] - tempTarget[0]
        yDistance = blinkyTile[1] - tempTarget[1]

        return (min(27, max(tempTarget[0] - xDistance, 0)), min(35, max(tempTarget[1] - yDistance, 0)))

    def clydeTarget(self, pacmanTile):
        distance = (self.sprite.center[0] - pacmanTile[0]) ** 2 + (self.sprite.center[0] - pacmanTile[0]) ** 2
        if distance > 64:
            clydeTarget = pacmanTile
        else:
            clydeTarget = self.scatterTile
        return clydeTarget
    
    def blinkyTarget(self, pacmanTile):
        return pacmanTile

    def release(self):
        self.sprite.center = self.releaseLocation
        self.released = True

    def move(self, board, opposite_directions, mode):
        pass

    def reset(self):
        self.sprite.center = self.startPos
        self.tile = findTile(self.sprite.center, self.tileSize)
        self.newLocation = self.sprite.center
        self.released = False