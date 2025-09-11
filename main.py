#26 long + 2 edges
#29 high + 2 edges + 3 above + 2 below
import pygame
import time
import random
import torch

from ghosts import Ghost
from boardUtils import *
from AI import TestAI

pygame.init()


#Find the new direction of an object given the board state
def getNewDirection(board, location, direction, target, oppositeDirections):
    #Find possible ways to move
    possibleDirections = findPossibleDirections(board, location)

    if oppositeDirections[direction] in possibleDirections:
        possibleDirections.remove(oppositeDirections[direction])

    #Find distance from each direction
    distances = []
    for i in possibleDirections:
        distances.append(newDistance(location, i, target))

    #Set direction to that
    index = distances.index(min(distances))
    return possibleDirections[index]

#Use AI to decide what move to make. Return a direction
def makeMoveAI(ai, location, ghostLocations, nearestPelletLocation, nearestSuperPelletLocation, score, ghostState, ghostMode, fruitVisible, currentDirection):
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

def displayWindow(window, board, tile, tileSize, font, score, textColor, lives):
    #Make the window white
    window.fill((255, 255, 255))

    drawBoard(board, tile, tileSize, window)

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

#Teleport either right or left. Return new tile as well as new center
def teleport(currentDirection, currentTile, currentCenter, tileSize):
    if currentTile == (0, 17) and currentDirection == "left": #Left teleport
        newTile = (27, 17)
        newCenter = findCenter(newTile, tileSize)
        return newTile, newCenter
    elif currentTile == (27, 17) and currentDirection == "right": #Right teleport
        newTile = (0, 17)
        newCenter = findCenter(newTile, tileSize)
        return newTile, newCenter
    else:
        return currentTile, currentCenter

#Initialize pacman
def initializePacman(pacmanSize, pacmanStartPosition):
    pacman = pygame.Rect(0, 0, pacmanSize, pacmanSize)
    pacman.center = pacmanStartPosition
    return pacman

def handleInput(lastInput, running):
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
    return lastInput, running

def run():
    pacmanColor = (255, 255, 0)#Yellow
    edibleGhostColor = (255, 255, 255)#White
    textColor = (255, 255, 255)#White

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

    #Define start locations
    pacmanStartPosition = (tileSize * 14, tileSize * 26.5)


    lives = 3

    #Initialize the tiles
    tile = pygame.Rect(0, 0, tileSize, tileSize)

    #Initialize the window
    window_size = (tileSize * 28, tileSize * 36)
    window = pygame.display.set_mode(window_size)
    pygame.display.set_caption("Pac-Man")

    pacman = initializePacman(pacmanSize, pacmanStartPosition)

    #Initialize the clock
    clock = pygame.time.Clock()

    #Create the board
    board = makeBoard()

    oppositeDirections = {"right":"left", "left":"right", "up":"down", "down":"up"}

    AIMode = False
    ai = TestAI()
    running = True

    lastInput = ""
    currentDirection = ""

    score = 0
    pelletsEaten = 0

    blinkySpeedUp = 0

    chaseMode = True
    cycle = 0
    timeSinceCycleStart = 0
    justSwitched = False

    superPelletMode = False
    superPelletStartTime = -1
    eatenGhosts = []

    globalCounter = 0

    releaseThresholds = [0, 7, 17, 32]

    fruitActive = False

    blinky = Ghost("blinky", startPos=(tileSize * 14, tileSize * 14.5), scatterTile=(25, 0), size=ghostSize, speed=ghostSpeed, releaseLocation=(tileSize * 14, tileSize * 14.5), releaseCounter=0, releaseThreshold=0, color=(255, 0, 0))
    pinky = Ghost("pinky", startPos=(tileSize * 14, tileSize * 17.5), scatterTile=(2, 0), size=14, speed=7.5, releaseLocation=(tileSize * 14, tileSize * 14.5), releaseCounter=0, releaseThreshold=0, color=(255, 184, 255))
    inky = Ghost("inky", startPos=(tileSize * 12, tileSize * 17.5), scatterTile=(27, 35), size=14, speed=7.5, releaseLocation=(tileSize * 14, tileSize * 14.5), releaseCounter=0, releaseThreshold=30, color=(0, 255, 255))
    clyde = Ghost("clyde", startPos=(tileSize * 16, tileSize * 17.5), scatterTile=(0, 35), size=14, speed=7.5, releaseLocation=(tileSize * 14, tileSize * 14.5), releaseCounter=0, releaseThreshold=60, color=(255, 184, 82))

    ghosts = [blinky, pinky, inky, clyde]

    #Temp var until I figure this out
    blinkyTile = (0, 0)

    time.sleep(5)
    while lives > 0 and running:
        if lastInput == "":#Just died or starting out
            for ghost in ghosts:
                ghost.released = False

            #Reset ghosts and pacman
            pacman.center = pacmanStartPosition

            for ghost in ghosts:
                ghost.center = ghost.startPos
                ghost.tile = findTile(ghost.center, tileSize)

        if not blinky.released: 
            blinky.release()

        if AIMode:
            if lastInput == "":
                lastInput = "left"
                currentDirection = "left"

            pacmanTile = findTile(pacman.center, tileSize)

            ghostLocations = []
            for ghost in ghosts:
                ghostLocations.append(findTile(ghost.center, tileSize))

            closestPellet = closestPoint(board, pacmanTile, [".", "I"])
            closestSuperPellet = closestPoint(board, pacmanTile, ["+"])

            if closestPellet == None:
                closestPellet = closestSuperPellet
            if closestSuperPellet == None:
                closestSuperPellet = closestPellet

            ghostState = 1 if superPelletMode else 0
            ghostMode = 1 if chaseMode else 0

            fruitVisible = 1 if fruitActive else 0
            lastInput = makeMoveAI(ai, pacmanTile, ghostLocations, closestPellet, closestSuperPellet, score, ghostState, ghostMode, fruitVisible, currentDirection)

        else:
            #Check for events
            lastInput, running = handleInput(lastInput, running)

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

        displayWindow(window, board, tile, tileSize, font, score, textColor, lives)

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
            pacmanTile, pacman.center = teleport(currentDirection, pacmanTile, pacman.center, tileSize)

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
                for ghost in ghosts:
                    if not ghost.released:
                        ghost.releaseCounter += 1
                        if ghost.releaseCounter >= ghost.releaseThreshold:
                            ghost.release()
            else:
                globalCounter += 1
                if globalCounter in releaseThresholds:
                    for ghost in ghosts:
                        if not ghost.released:
                            ghost.release()
                            break                


        elif board[pacmanTile[1]][pacmanTile[0]] == "I": #Dot, intersection
            board[pacmanTile[1]] = board[pacmanTile[1]][:pacmanTile[0]] + "i" + board[pacmanTile[1]][pacmanTile[0] + 1:]
            score += 1
            pelletsEaten += 1
            if 244 - pelletsEaten in speedUpThresholds:
                blinkySpeedUp += 1
            if lives == initialLives:
                for ghost in ghosts:
                    if not ghost.released:
                        ghost.releaseCounter += 1
                        if ghost.releaseCounter >= ghost.releaseThreshold:
                            ghost.release()
            else:
                globalCounter += 1
                if globalCounter in releaseThresholds:
                    for ghost in ghosts:
                        if not ghost.released:
                            ghost.release()
                            break


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
                for ghost in ghosts:
                    if not ghost.released:
                        ghost.releaseCounter += 1
                        if ghost.releaseCounter >= ghost.releaseThreshold:
                            ghost.release()
            else:
                globalCounter += 1
                if globalCounter in releaseThresholds:
                    for ghost in ghosts:
                        if not ghost.released:
                            ghost.release()
                            break

        for ghost in ghosts:
            if not ghost.released: continue

            #Find ghosts new location
            ghost.newLocation = ghost.center

            if currentDirection != "":#Started

                if justSwitched:
                    ghost.direction = oppositeDirections[ghost.direction]

                if superPelletMode:
                    #Set target to random
                    randomTarget = (random.randint(0, 27), random.randint(0, 35))
                    ghost.target = randomTarget
                elif chaseMode or (ghost == "blinky" and 244 - pelletsEaten <= speedUpThresholds[0]): #Blinky has no scatter mode after speeding up
                    ghost.target = ghost.chooseTarget(chaseMode, pacmanTile, blinkyTile)
                        
                else: #Scatter mode
                    ghost.target = ghost.scatterTile

                if superPelletMode:
                    speed = ghostSpeedFrightened * tileSize / framerate
                if ghost == "blinky":
                    speed = (ghostSpeed + .5 * blinkySpeedUp) * tileSize / framerate
                else:
                    speed = ghostSpeed * tileSize / framerate
                
                if willPassCenter(ghost.center, ghost.direction, speed, tileSize):
                    #Get new direction
                    ghost.direction = getNewDirection(board, ghost.tile, ghost.direction, ghost.target, oppositeDirections)

                    #Center ghost on tile
                    ghost.center = findCenter(ghost.tile, tileSize)


                ghost.newLocation = getNewObjectLocation(ghost.center, ghost.direction, speed, tileSize)
        justSwitched = False
        
        #Dont walk through walls
        for ghost in ghosts:
            if not ghost.released:
                continue

            ghost.newLocation = getLegalLocation(board, ghost.newLocation, tileSize, ghostSize)
            ghost.center = ghost.newLocation
            ghost.tile = findTile(ghost.center, tileSize)

        #Teleport pads
        for ghost in ghosts:
            if not ghost.released:
                continue
            
            if board[ghost.tile[1]][ghost.tile[0]] == "X": #On teleport
                ghost.tile, ghost.center = teleport(ghost.direction, ghost.tile, ghost.center, tileSize)

        #Update tile
        for ghost in ghosts:
            if not ghost.released:
                continue
            
            ghost.tile = findTile(ghost.center, tileSize)

        #Check if pacman or ghosts are touching
        for ghost in ghosts:
            if not ghost.released:
                continue
            
            if pacmanTile == ghost.tile:
                if superPelletMode and ghost not in eatenGhosts:
                    #Eat ghosts
                    score += 100
                    eatenGhosts.append(ghost)
            
                    #Reset ghost
                    ghost.center = (tileSize * 14, tileSize * 14.5)
                    ghost.tile = findTile(ghost.center, tileSize)
                else:
                    lives -= 1
                    lastInput = ""
                    globalCounter = 0
                    superPelletMode = False

        #Add pacman
        pygame.draw.rect(window, pacmanColor, pacman)

        #Add ghosts
        for ghost in ghosts:
            if superPelletMode and ghost not in eatenGhosts:
                ghost.draw(window, edibleGhostColor)
            else:
                ghost.draw(window, ghost.color)



        #Update time since ghosts switched between chase and scatter modes. Dont update if in super pellet mode (i think)
        if lastInput != "" and not superPelletMode:
            timeSinceCycleStart += 1 / framerate

        #Update the board
        pygame.display.update()

        #Limit the frame rate
        clock.tick(framerate)

    pygame.quit()

run()
