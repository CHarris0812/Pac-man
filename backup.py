#26 long + 2 edges
#29 high + 2 edges + 3 above + 2 below
import pygame
import time
import random
from AI import TestAI
import torch

pygame.init()


#Read the given text file and return it as a list of strings
def makeBoard():
    b = []
    f = open("initialBoard.txt", "r")
    for line in f:
        line = line.replace("\n", "")
        b.append(line)
    return b

#Find which tile an object is currently on
def findTile(center, tileSize):
    return (int(center[0] // tileSize), int(center[1] // tileSize))

#Find the new location of an object
def getNewObjectLocation(location, direction, speed, tileSize):
    if direction == "right":
        return (location[0] + speed, ((location[1] // tileSize) + .5) * tileSize)
    if direction == "left":
        return (location[0] - speed, ((location[1] // tileSize) + .5) * tileSize)
    if direction == "up":
        return (((location[0] // tileSize) + .5) * tileSize, location[1] - speed)
    if direction == "down":
        return (((location[0] // tileSize) + .5) * tileSize, location[1] + speed)
    return location

#Find the tile that each edge of an object is on
def findEdgeTiles(center, tileSize, objectSize):
    edges = []
    edges.append(findTile((center[0], center[1] + objectSize / 2), tileSize))
    edges.append(findTile((center[0], center[1] - objectSize / 2), tileSize))
    edges.append(findTile((center[0] + objectSize / 2, center[1]), tileSize))
    edges.append(findTile((center[0] - objectSize / 2, center[1]), tileSize))
    return edges

#Finds the center of a given tile
def findCenter(tile, tileSize):
    return (int((tile[0] + .5) * tileSize), int((tile[1] + .5) * tileSize))

#Checks if turning in a given direction is legal
def isLegalMove(board, edges, direction):
    legal = True
    for edge in edges:
        if direction == "right":
            if len(board[0]) != edge[0] + 1:
                if board[edge[1]][edge[0] + 1] == "%":
                    legal = False
        if direction == "left":
            if board[edge[1]][edge[0] - 1] == "%":
                legal = False
        if direction == "up":
            if board[edge[1] - 1][edge[0]] == "%":
                legal = False
        if direction == "down":
            if board[edge[1] + 1][edge[0]] == "%":
                legal = False
    return legal

#Check if the object has passed into a wall. If so, set its new location
def getLegalLocation(board, location, tileSize, objectSize):
    edgeTiles = findEdgeTiles(location, tileSize, objectSize)

    #Set validLocation to the edge not in the tile
    validLocation = -1
    for e in range(len(edgeTiles)):
        if edgeTiles[e][0] == len(board[0]): #Right teleport pad
            validLocation = e
        elif board[edgeTiles[e][1]][edgeTiles[e][0]] == "%":
            validLocation = e

    #If would walk through edge, stop
    if validLocation != -1:
        if validLocation == 0:
            newTile = edgeTiles[1]
            location = findCenter(newTile, tileSize)
        else:
            newTile = edgeTiles[0]
            location = findCenter(newTile, tileSize)

    return location

#At a given tile, determine which directions are legal
def findPossibleDirections(board, tile):
    row = tile[1]
    col = tile[0]


    possible = []
    if board[row + 1][col] not in ["G", "%"]:
        possible.append("down")

    if board[row - 1][col] not in ["G", "%"]:
        possible.append("up")

    if col + 1 == len(board[row]): #Walked through teleport pad
        possible.append("right")
    elif board[row][col + 1] not in ["G", "%"]:
        possible.append("right")

    if col - 1 == 0: #Walked through teleport pad
        possible.append("left")
    elif board[row][col - 1] not in ["G", "%"]:
        possible.append("left")
    return possible

#Find the manhattan distance after moving
def manhattanDistance(board, startTile, direction, endTile):
    if direction == "left":
        newTile = (startTile[0] - 1, startTile[1])
    if direction == "right":
        newTile = (startTile[0] + 1, startTile[1])
    if direction == "up":
        newTile = (startTile[0], startTile[1] - 1)
    if direction == "down":
        newTile = (startTile[0], startTile[1] + 1)

    return abs(newTile[0] - endTile[0]) + abs(newTile[1] - endTile[1])

#Check if a given movement will cause the object to pass the center of a tile
def willPassCenter(location, direction, speed, tileSize):
    #Figure out whether X or Y coordinate is important
    if direction in ["up", "down"]:
        location = location[1]
    else:
        location = location[0]

    #Check whether the object will move in the positive or negative direction
    if direction in ["down", "right"]:
        change = speed
    else:
        change = -1 * speed


    if ((location % tileSize) <= tileSize / 2 and (location % tileSize) + change > tileSize / 2) or ((location % tileSize) >= tileSize / 2 and (location % tileSize) + change < tileSize / 2):
        return True
    return False

#Check if the ghosts should switch between chase and scatter modes.
def shouldSwitchModes(cycle, timeSinceCycleStart, chaseMode, chaseTimes, scatterTimes):
    shouldSwitch = False

    if chaseMode:
        #If chased for necessary time
        if timeSinceCycleStart > chaseTimes[cycle]:
            #Scatter
            chaseMode = False
            cycleStart = time.time()
            shouldSwitch = True
    #If scatter mode
    else:
        if timeSinceCycleStart > scatterTimes[cycle]:
            #Chase
            chaseMode = True
            cycleStart = time.time()
            shouldSwitch = True
    
    return chaseMode

#Find the new direction of an object given the board state
def getNewDirection(board, location, direction, target):
    #Find possible ways to move
    possibleDirections = findPossibleDirections(board, location)

    if oppositeDirections[direction] in possibleDirections:
        possibleDirections.remove(oppositeDirections[direction])

    #Find distance from each direction
    distances = []
    for i in possibleDirections:
        distances.append(manhattanDistance(board, location, i, target))

    #Set direction to that
    index = distances.index(min(distances))
    return possibleDirections[index]

#Use AI to decide what move to make. Return a direction
def makeMoveAI(ai, location, ghostLocations, nearestPelletLocation, nearestSuperPelletLocation, score, ghostState, ghostMode, fruitVisible):
    combinedGhostLocations = [value for tuple in ghostLocations for value in tuple]
    combinedGhostLocations = [i * 1.0 for i in combinedGhostLocations]

    formattedLocation = [location[0] * 1.0, location[1] * 1.0]
    formattedPelletLocation = [nearestPelletLocation[0] * 1.0, nearestPelletLocation[1] * 1.0] + [nearestSuperPelletLocation[0] * 1.0, nearestSuperPelletLocation[1] * 1.0]
    formattedInfo = [score * 1.0, ghostState * 1.0, ghostMode * 1.0, fruitVisible * 1.0, ]

    input = torch.tensor(formattedLocation + combinedGhostLocations + formattedPelletLocation + formattedInfo)
    direction = ai.run(input)
    if direction == "none":
        direction = currentDirection
    return direction

def closestPoint(board, location, symbols):
    distances = [[(location[1] - i) ** 2 + (location[0] - j) ** 2 for j in range(len(board[i]))] for i in range(len(board))]
    minVal = 10000000
    minLoc = None

    for i in range(len(board)):
        for j in range(len(board[i])):
            if board[i][j] in symbols:
                if distances[i][j] < minVal:
                    minVal = distances[i][j]
                    minLoc = (j, i)

    return minLoc



pacmanColor = (255, 255, 0)#Yellow
wallColor = (0, 0, 255)#Blue
emptyColor = (0, 0, 0)#Black
dotColor = (211, 211, 211)#Gray
offScreenColor = (0, 0, 0)#Black
ghostEntranceColor = (255, 192, 203)#Pink
tunnelColor = (0, 0, 0)#Black
intersectionWithDotColor = (0, 255, 0)#Green
intersectionWithoutDotColor = (255, 0, 255)#Purple
superPelletColor = (0, 255, 255)#Teal
edibleGhostColor = (255, 255, 255)#White
textColor = (255, 255, 255)#White
blinkyColor = (255, 0, 0)#Red
inkyColor = (0, 255, 255)#Aqua
pinkyColor = (255, 184, 255)#Pink
clydeColor = (255, 184, 82)#Orange


tileSize = 16
pacmanSize = 14
ghostSize = 14
pacmanSpeed = 8#Tiles/sec
ghostSpeed = 7.5#Tiles/sec
pacmanSpeedFrightened = 9
ghostSpeedFrightened = 5

framerate = 60#fps
font = pygame.font.Font("PressStart2P-Regular.ttf", int(tileSize * 1.5))

initialLives = 3
scatterTimes = [7, 7, 5, 5]#Seconds
chaseTimes = [20, 20, 20, 20, 1000000]#Seconds
superPelletLength = 10#Seconds
speedUpThresholds = [40, 20]

#Define scatter tiles
blinkyScatterTile = (25, 0)
inkyScatterTile = (27, 35)
pinkyScatterTile = (2, 0)
clydeScatterTile = (0, 35)

#Define start locations
blinkyStartPosition = (tileSize * 14, tileSize * 14.5)
pinkyStartPosition = (tileSize * 14, tileSize * 17.5)
inkyStartPosition = (tileSize * 12, tileSize * 17.5)
clydeStartPosition = (tileSize * 16, tileSize * 17.5)
pacmanStartPosition = (tileSize * 14, tileSize * 26.5)


lives = 3

#Initialize the tiles
tile = pygame.Rect(0, 0, tileSize, tileSize)

#Initialize the window
window_size = (tileSize * 28, tileSize * 36)
window = pygame.display.set_mode(window_size)
pygame.display.set_caption("Pac-Man")

#Initialize pacman
pacman = pygame.Rect(0, 0, pacmanSize, pacmanSize)
pacman.center = pacmanStartPosition

#Initialize red ghost
blinky = pygame.Rect(0, 0, ghostSize, ghostSize)
blinky.center = blinkyStartPosition

#Initialize pink ghost
pinky = pygame.Rect(0, 0, ghostSize, ghostSize)
pinky.center = pinkyStartPosition

#Initialize teal ghost
inky = pygame.Rect(0, 0, ghostSize, ghostSize)
inky.center = inkyStartPosition

#Initialize pink ghost
clyde = pygame.Rect(0, 0, ghostSize, ghostSize)
clyde.center = clydeStartPosition

#Initialize the clock
clock = pygame.time.Clock()

#Create the board
board = makeBoard()

oppositeDirections = {"right":"left", "left":"right", "up":"down", "down":"up"}

AIMode = True
ai = TestAI()
running = True

lastInput = ""
currentDirection = ""

score = 0
pelletsEaten = 0

blinkyDirection = "left"
blinkySpeedUp = 0

pinkyDirection = "left"

inkyDirection = "left"

clydeDirection = "left"

chaseMode = True
cycle = 0
timeSinceCycleStart = 0
justSwitched = False

superPelletMode = False
superPelletStartTime = -1
eatenGhosts = []

dummyCounter = 0
globalCounter = 0
pinkyCounter = 0
inkyCounter = 0
clydeCounter = 0

pinkyThreshold = 0
inkyThreshold = 30
clydeThreshold = 60

releaseThresholds = [0, 7, 17, 32]

fruitActive = False

ghosts = ["blinky", "pinky", "inky", "clyde"]
releasedGhosts = []
time.sleep(5)
while lives > 0:
    if lastInput == "":#Just died or starting out
        releasedGhosts = []

        #Reset ghosts and pacman
        pacman.center = pacmanStartPosition
        blinky.center = blinkyStartPosition
        pinky.center = pinkyStartPosition
        inky.center = inkyStartPosition
        clyde.center = clydeStartPosition
    if releasedGhosts == [] and lastInput != "":
        releasedGhosts = ["blinky"]
    if AIMode:
        if lastInput == "":
            lastInput = "left"
            currentDirection = "left"

        pacmanTile = findTile(pacman.center, tileSize)

        ghostLocations = []
        for ghost in ghosts:
            ghostLocations.append(findTile(eval(ghost).center, tileSize))

        closestPellet = closestPoint(board, pacmanTile, [".", "I"])
        closestSuperPellet = closestPoint(board, pacmanTile, ["+"])

        if closestPellet == None:
            closestPellet = closestSuperPellet
        if closestSuperPellet == None:
            closestSuperPellet = closestPellet

        ghostState = 1 if superPelletMode else 0
        ghostMode = 1 if chaseMode else 0

        fruitVisible = 1 if fruitActive else 0
        lastInput = makeMoveAI(ai, pacmanTile, ghostLocations, closestPellet, closestSuperPellet, score, ghostState, ghostMode, fruitVisible)

    else:
        #Check for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    lastInput = "up"
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    lastInput = "down"
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    lastInput = "left"
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    lastInput = "right"

    #Switch between chase and scatter modes
    tempChaseMode = shouldSwitchModes(cycle, timeSinceCycleStart, chaseMode, chaseTimes, scatterTimes)
    if tempChaseMode != chaseMode:
        chaseMode = tempChaseMode
        justSwitched = True
        timeSinceCycleStart = 0

    #End super pellet mode
    if superPelletMode:
        if time.time() - superPelletStartTime > superPelletLength:
            superPelletMode = False

    #Make the window white
    window.fill((255, 255, 255))

    #Draw the board
    for row in range(len(board)):
        for item in range(len(board[0])):
            tile.center = (tileSize // 2 + item * tileSize, tileSize // 2 + row * tileSize)
            if board[row][item] == "%":#Wall
                pygame.draw.rect(window, wallColor, tile)
            elif board[row][item] == ".":#Dot
                pygame.draw.rect(window, dotColor, tile)
            elif board[row][item] == "0":#Empty
                pygame.draw.rect(window, emptyColor, tile)
            elif board[row][item] == "-":#Above or below screen
                pygame.draw.rect(window, offScreenColor, tile)
            elif board[row][item] == "G":#Ghost entrance
                pygame.draw.rect(window, ghostEntranceColor, tile)
            elif board[row][item] == "X":#Tunnel
                pygame.draw.rect(window, tunnelColor, tile)
            elif board[row][item] == "I":#Intersection with dot
                pygame.draw.rect(window, intersectionWithDotColor, tile)
            elif board[row][item] == "i":#Intersection without dot
                pygame.draw.rect(window, intersectionWithoutDotColor, tile)
            elif board[row][item] == "+":#Super pellet
                pygame.draw.rect(window, superPelletColor, tile)
            else:
                pass


    #Display score
    scoreText = font.render("Score: " + str(score), True, textColor)
    scoreRect = scoreText.get_rect()
    scoreRect.topleft = (0, 0)
    window.blit(scoreText, scoreRect)

    #Display lives
    livesText = font.render("Lives: " + str(lives), True, textColor)
    livesRect = livesText.get_rect()
    livesRect.topleft = (200, 0)
    window.blit(livesText, livesRect)

    #Start moving
    if currentDirection == "" and lastInput != "":
        if lastInput == "left":
            currentDirection = lastInput
        elif lastInput == "right":
            currentDirection = lastInput


    #Check if move is legal    
    edgeTiles = findEdgeTiles(pacman.center, tileSize, pacmanSize)
    if isLegalMove(board, edgeTiles, lastInput):
        currentDirection = lastInput

    #Move pacman
    pacmanLocation = pacman.center
    newPacmanLocation = getNewObjectLocation(pacman.center, currentDirection, pacmanSpeed * tileSize / framerate, tileSize)
    
    #Prevent walking through walls
    newPacmanLocation = getLegalLocation(board, newPacmanLocation, tileSize, pacmanSize)
    pacman.center = newPacmanLocation

    #Teleport pads for pacman
    pacmanTile = findTile(newPacmanLocation, tileSize)
    if board[pacmanTile[1]][pacmanTile[0]] == "X": #On teleport
        if pacmanTile == (0, 17): #Left teleport
            if currentDirection == "left": #Moving left
                pacmanTile = (27, 17)
                pacman.center = findCenter(pacmanTile, tileSize)
        elif pacmanTile == (27, 17): #Right teleport
            if currentDirection == "right":
                pacmanTile = (0, 17)
                pacman.center = findCenter(pacmanTile, tileSize)

    #Update tiles based on pacmans position
    pacmanTile = findTile(pacman.center, tileSize)
    
    #Change dot to empt y
    if board[pacmanTile[1]][pacmanTile[0]] == ".": #Dot, not intersection
        board[pacmanTile[1]] = board[pacmanTile[1]][:pacmanTile[0]] + "0" + board[pacmanTile[1]][pacmanTile[0] + 1:]
        score += 1
        pelletsEaten += 1
        if 244 - pelletsEaten in speedUpThresholds:
            blinkySpeedUp += 1
        if lives == initialLives:
            if "pinky" not in releasedGhosts:
                pinkyCounter += 1
            elif "inky" not in releasedGhosts:
                inkyCounter += 1
            elif "clyde" not in releasedGhosts:
                clydeCounter += 1

            if pinkyCounter >= pinkyThreshold and "pinky" not in releasedGhosts:
                pinky.center = blinkyStartPosition
                releasedGhosts.append("pinky")
            if inkyCounter >= inkyThreshold and "inky" not in releasedGhosts:
                inky.center = blinkyStartPosition
                releasedGhosts.append("inky")
            if clydeCounter >= clydeThreshold and "clyde" not in releasedGhosts:
                clyde.center = blinkyStartPosition
                releasedGhosts.append("clyde")
        else:
            globalCounter += 1
            if globalCounter in releaseThresholds:
                ghostToBeReleased = ghosts[releaseThresholds.index(globalCounter)]
                exec(ghostToBeReleased + ".center = blinkyStartPosition")
                exec("releasedGhosts.append(\"" + ghostToBeReleased + "\")")


    elif board[pacmanTile[1]][pacmanTile[0]] == "I": #Dot, intersection
        board[pacmanTile[1]] = board[pacmanTile[1]][:pacmanTile[0]] + "i" + board[pacmanTile[1]][pacmanTile[0] + 1:]
        score += 1
        pelletsEaten += 1
        if 244 - pelletsEaten in speedUpThresholds:
            blinkySpeedUp += 1
        if lives == initialLives:
            if "pinky" not in releasedGhosts:
                pinkyCounter += 1
            elif "inky" not in releasedGhosts:
                inkyCounter += 1
            elif "clyde" not in releasedGhosts:
                clydeCounter += 1

            if pinkyCounter >= pinkyThreshold and "pinky" not in releasedGhosts:
                pinky.center = blinkyStartPosition
                releasedGhosts.append("pinky")
            if inkyCounter >= inkyThreshold and "inky" not in releasedGhosts:
                inky.center = blinkyStartPosition
                releasedGhosts.append("inky")
            if clydeCounter >= clydeThreshold and "clyde" not in releasedGhosts:
                clyde.center = blinkyStartPosition
                releasedGhosts.append("clyde")
        else:
            globalCounter += 1
            if globalCounter in releaseThresholds:
                ghostToBeReleased = ghosts[releaseThresholds.index(globalCounter)]
                exec(ghostToBeReleased + ".center = blinkyStartPosition")
                exec("releasedGhosts.append(\"" + ghostToBeReleased + "\")")

    elif board[pacmanTile[1]][pacmanTile[0]] == "+": #Super pellet
        board[pacmanTile[1]] = board[pacmanTile[1]][:pacmanTile[0]] + "0" + board[pacmanTile[1]][pacmanTile[0] + 1:]
        superPelletMode = True
        superPelletStartTime = time.time()
        score += 10
        pelletsEaten += 1
        if 244 - pelletsEaten in speedUpThresholds:
            blinkySpeedUp += 1
        eatenGhosts = []
        justSwitched = True
        if lives == initialLives:
            if "pinky" not in releasedGhosts:
                pinkyCounter += 1
            elif "inky" not in releasedGhosts:
                inkyCounter += 1
            elif "clyde" not in releasedGhosts:
                clydeCounter += 1

            if pinkyCounter >= pinkyThreshold and "pinky" not in releasedGhosts:
                pinky.center = blinkyStartPosition
                releasedGhosts.append("pinky")
            if inkyCounter >= inkyThreshold and "inky" not in releasedGhosts:
                inky.center = blinkyStartPosition
                releasedGhosts.append("inky")
            if clydeCounter >= clydeThreshold and "clyde" not in releasedGhosts:
                clyde.center = blinkyStartPosition
                releasedGhosts.append("clyde")
        else:
            globalCounter += 1
            if globalCounter in releaseThresholds:
                ghostToBeReleased = ghosts[releaseThresholds.index(globalCounter)]
                exec(ghostToBeReleased + ".center = blinkyStartPosition")
                exec("releasedGhosts.append(\"" + ghostToBeReleased + "\")")

    for ghost in releasedGhosts:
        #Find ghosts new location
        exec("new" + ghost.capitalize() + "Location = " + ghost + ".center")
        if currentDirection != "":#Started

            if justSwitched:
                exec(ghost + "Direction = oppositeDirections[" + ghost + "Direction]")

            if superPelletMode:
                #Set target to random
                randomTarget = (random.randint(0, 27), random.randint(0, 35))
                exec(ghost + "Target = " + str(randomTarget))
            elif chaseMode or (ghost == "blinky" and 244 - pelletsEaten <= speedUpThresholds[0]): #Blinky has no scatter mode after speeding up
                #Find target
                if ghost == "blinky":
                    blinkyTarget = pacmanTile
                elif ghost == "pinky":
                    if currentDirection == "left":
                        pinkyTarget = (max(0, pacmanTile[0] - 4), pacmanTile[1])
                    elif currentDirection == "right":
                        pinkyTarget = (min(27, pacmanTile[0] + 4), pacmanTile[1])
                    elif currentDirection == "up":
                        pinkyTarget = (pacmanTile[0], max(0, pacmanTile[1] - 4))
                    elif currentDirection == "down":
                        pinkyTarget = (pacmanTile[0], min(35, pacmanTile[1] + 4))
                elif ghost == "inky":
                    if currentDirection == "left":
                        tempTarget = (max(0, pacmanTile[0] - 4), pacmanTile[1])
                    elif currentDirection == "right":
                        tempTarget = (min(27, pacmanTile[0] + 4), pacmanTile[1])
                    elif currentDirection == "up":
                        tempTarget = (pacmanTile[0], max(0, pacmanTile[1] - 4))
                    elif currentDirection == "down":
                        tempTarget = (pacmanTile[0], min(35, pacmanTile[1] + 4))

                    xDistance = blinkyTile[0] - tempTarget[0]
                    yDistance = blinkyTile[1] - tempTarget[1]

                    inkyTarget = (min(27, max(tempTarget[0] - xDistance, 0)), min(35, max(tempTarget[1] - yDistance, 0)))
                elif ghost == "clyde":
                    distance = (newClydeLocation[0] - pacmanTile[0]) ** 2 + (newClydeLocation[0] - pacmanTile[0]) ** 2
                    if distance > 64:
                        clydeTarget = pacmanTile
                    else:
                        clydeTarget = clydeScatterTile
            else: #Scatter mode
                #Find target
                exec(ghost + "Target = " + ghost + "ScatterTile")

            if superPelletMode:
                speed = ghostSpeedFrightened * tileSize / framerate
            if ghost == "blinky":
                speed = (ghostSpeed + .5 * blinkySpeedUp) * tileSize / framerate
            else:
                speed = ghostSpeed * tileSize / framerate
                
            if willPassCenter(eval(ghost).center, eval(ghost + "Direction"), speed, tileSize):
                #Get new direction
                exec(ghost + "Direction = getNewDirection(board, " + ghost + "Tile, " + ghost + "Direction, " + ghost + "Target)")

                #Center ghost on tile
                eval(ghost).center = findCenter(eval(ghost + "Tile"), tileSize)


            exec("new" + ghost.capitalize() + "Location = getNewObjectLocation(" + ghost + ".center, " + ghost + "Direction, speed, tileSize)")
    justSwitched = False
        
    #Dont walk through walls
    for ghost in releasedGhosts:
        exec("new" + ghost.capitalize() + "Location = getLegalLocation(board, new" + ghost.capitalize() + "Location, tileSize, ghostSize)")
        exec(ghost + ".center = new" + ghost.capitalize() + "Location")
        exec(ghost + "Tile = findTile(" + ghost + ".center, tileSize)")

    #Teleport pads
    for ghost in releasedGhosts:
        if board[eval(ghost + "Tile[1]")][eval(ghost + "Tile[0]")] == "X": #On teleport
            if eval(ghost + "Tile") == (0, 17): #Left teleport
                if eval(ghost + "Direction") == "left": #Moving left
                    exec(ghost + "Tile = (27, 17)")
                    exec(ghost + ".center = findCenter(" + ghost + "Tile, tileSize)")
            elif eval(ghost + "Tile") == (27, 17): #Right teleport
                if blinkyDirection == "right":
                    exec(ghost + "Tile = (0, 17)")
                    exec(ghost + ".center = findCenter(" + ghost + "Tile, tileSize)")


    #Update tile
    for ghost in releasedGhosts:
        exec(ghost + "Tile = findTile(" + ghost + ".center, tileSize)")

    #Check if pacman or ghosts are touching
    for ghost in releasedGhosts:
        if pacmanTile == eval(ghost + "Tile"):
            if superPelletMode and ghost not in eatenGhosts:
                #Eat ghosts
                score += 100
                eatenGhosts.append(ghost)
            
                #Reset ghost
                exec(ghost + ".center = (tileSize * 14, tileSize * 14.5)")
                exec(ghost + "Tile = findTile(" + ghost + ".center, tileSize)")
            else:
                lives -= 1
                lastInput = ""
                globalCounter = 0
                superPelletMode = False
                justDied = True

    #Add pacman
    pygame.draw.rect(window, pacmanColor, pacman)

    #Add ghosts
    for ghost in ghosts:
        if superPelletMode and ghost not in eatenGhosts: #Pinky can still be eaten
            pygame.draw.rect(window, edibleGhostColor, eval(ghost))
        else:
            pygame.draw.rect(window, eval(ghost + "Color"), eval(ghost))



    #Update time since ghosts switched between chase and scatter modes. Dont update if in super pellet mode (i think)
    if lastInput != "" and not superPelletMode:
        timeSinceCycleStart += 1 / framerate

    #Update the board
    pygame.display.update()

    #Limit the frame rate
    clock.tick(framerate)

pygame.quit()
