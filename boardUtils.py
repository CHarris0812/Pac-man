import pygame

# Read the given text file and return it as a list of strings
def makeBoard(file="initialBoard.txt"):
    b = []
    with open(file, "r") as f:
        for line in f:
            line = line.strip()
            b.append(line)
    return b

# Find which tile an object is currently on
def findTile(center, tileSize):
    return (int(center[0] // tileSize), int(center[1] // tileSize))

# Find the new location of an object
def getNewObjectLocation(location, direction, speed, tileSize):
    if direction == "right":
        return (location[0] + speed, ((location[1] // tileSize) + 0.5) * tileSize)
    if direction == "left":
        return (location[0] - speed, ((location[1] // tileSize) + 0.5) * tileSize)
    if direction == "up":
        return (((location[0] // tileSize) + 0.5) * tileSize, location[1] - speed)
    if direction == "down":
        return (((location[0] // tileSize) + 0.5) * tileSize, location[1] + speed)
    return location

# Find the tile that each edge of an object is on
def findEdgeTiles(center, tileSize, objectSize):
    edges = [
        findTile((center[0], center[1] + objectSize / 2), tileSize),
        findTile((center[0], center[1] - objectSize / 2), tileSize),
        findTile((center[0] + objectSize / 2, center[1]), tileSize),
        findTile((center[0] - objectSize / 2, center[1]), tileSize)
    ]
    return edges

# Finds the center of a given tile
def findCenter(tile, tileSize):
    return (int((tile[0] + 0.5) * tileSize), int((tile[1] + 0.5) * tileSize))

# Checks if turning in a given direction is legal
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

# Check if the object has passed into a wall. If so, set its new location
def getLegalLocation(board, location, tileSize, objectSize):
    edgeTiles = findEdgeTiles(location, tileSize, objectSize)

    validLocation = -1
    for e in range(len(edgeTiles)):
        if edgeTiles[e][0] == len(board[0]):  # Right teleport pad
            validLocation = e
        elif board[edgeTiles[e][1]][edgeTiles[e][0]] == "%":
            validLocation = e

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

# Find the distance after moving
def newDistance(startTile, direction, endTile):
    x, y = startTile
    if direction == "left":
        x -= 1
    if direction == "right":
        x += 1
    if direction == "up":
        y -= 1
    if direction == "down":
        y += 1
    return (x - endTile[0]) ** 2 + (y - endTile[1]) ** 2

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
    if chaseMode:
        #If chased for necessary time
        if timeSinceCycleStart > chaseTimes[cycle]:
            #Scatter
            chaseMode = False
    #If scatter mode
    else:
        if timeSinceCycleStart > scatterTimes[cycle]:
            #Chase
            chaseMode = True
    
    return chaseMode

# Find closest point with given symbols
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

#Draw the board
def drawBoard(board, tile, tileSize, window):
    wallColor = (0, 0, 255)#Blue
    emptyColor = (0, 0, 0)#Black
    dotColor = (211, 211, 211)#Gray
    offScreenColor = (0, 0, 0)#Black
    ghostEntranceColor = (255, 192, 203)#Pink
    tunnelColor = (0, 0, 0)#Black
    intersectionWithDotColor = (0, 255, 0)#Green
    intersectionWithoutDotColor = (255, 0, 255)#Purple
    superPelletColor = (0, 255, 255)#Teal
    
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