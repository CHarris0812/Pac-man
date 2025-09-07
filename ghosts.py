

class Ghost:
    def __init__(self, name, startPos, scatterTile, size, speed):
        self.name = name
        self.center = startPos
        self.scatterTile = scatterTile
        self.size = size
        self.speed = speed
        self.direction = "left"
        self.target = scatterTile
        self.tile = findTile(self.center, size)
        self.released = False
        self.eaten = False

    def update_tile(self):
        pass

    def choose_target(self, chaseMode, pacmanTile, blinkyTile):
        if not chaseMode: return self.scatterTile
        elif self.name == "pinky": return self.pinkyTarget(pacmanTile)
        elif self.name == "inky": return self.inkyTarget(pacmanTile, blinkyTile)
        elif self.name == "clyde": return self.clydeTarget(pacmanTile)
        else: return self.blinkyTarget()

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
        if self.direction == "left":
            tempTarget = (max(0, pacmanTile[0] - 4), pacmanTile[1])
        elif self.direction == "right":
            tempTarget = (min(27, pacmanTile[0] + 4), pacmanTile[1])
        elif self.direction == "up":
            tempTarget = (pacmanTile[0], max(0, pacmanTile[1] - 4))
        elif self.direction == "down":
            tempTarget = (pacmanTile[0], min(35, pacmanTile[1] + 4))

        xDistance = blinkyTile[0] - tempTarget[0]
        yDistance = blinkyTile[1] - tempTarget[1]

        return (min(27, max(tempTarget[0] - xDistance, 0)), min(35, max(tempTarget[1] - yDistance, 0)))

    def clydeTarget(self, pacmanTile):
        distance = (self.center[0] - pacmanTile[0]) ** 2 + (self.center[0] - pacmanTile[0]) ** 2
        if distance > 64:
            clydeTarget = pacmanTile
        else:
            clydeTarget = self.scatterTile
        return clydeTarget
    
    def blinkyTarget(self, pacmanTile):
        return pacmanTile

    def move(self, board, opposite_directions, mode):
        pass
