from hlt import *
from networking import *
import logging
from math import pi

##### Logging Setup
import logging
logger = logging.getLogger('bot')
logger.setLevel(logging.DEBUG)	

base_formatter = logging.Formatter("%(asctime)s : %(levelname)s %(message)s")
log_file_name = 'bot.debug'
hdlr = logging.FileHandler(log_file_name)
hdlr.setFormatter(base_formatter)
hdlr.setLevel(logging.DEBUG)
logger.addHandler(hdlr)


logger.info("Initialized logging")


myID, gameMap = getInit()
sendInit("MyPythonBot")
turnCounter = 0

def evaluateSite(site):
	str = site.strength
	if str < 1:
		str = 1
	return site.production/str

def getBestDir(map, location):
	bestDir = None
	bestValue = 0
	
	base = int(random.random()*4)
	dir_list = CARDINALS
	random.shuffle(dir_list)
	logger.debug(dir_list)
	for dir in dir_list:
		site = map.getSite(location, dir)
		value = evaluateSite(site)
		if site.owner != myID and (not bestDir or bestValue < value):
			logger.debug("Found new bestDir: %s" % dir)
			bestDir = dir
			bestValue = value
	return bestDir
	

def getDirForSquare(map, location):
	t = map.getTerritory(myID)
	center = t.getCenter()
	angle = map.getAngle(center, location)
	
	
	dir = STILL
	
	site = map.getSite(location)
	if site.friends < 4:
		dir = getBestDir(map, location)
	elif angle < pi/4.0 and angle > -1*pi/4.0:
		if angle > 0:
			dir = SOUTH
		elif angle < 0:
			dir =  NORTH
		else:
			dir =  EAST
	elif angle > pi/4.0 and angle < 3*pi/4.0:
		if angle > pi/2.0:
			dir =  WEST
		elif angle < pi/2.0:
			dir =  EAST
		else:
			dir =  NORTH
	elif angle < pi/-4.0 and angle > -3*pi/4.0:
		if angle > pi/-2.0:
			dir =  EAST
		elif angle < pi/-2.0:
			dir =  WEST
		else:
			dir =  SOUTH
	elif angle > 3*pi/4.0 or angle < -3*pi/4.0:
		if angle > 0:
			dir =  NORTH
		elif angle < 0:
			dir =  SOUTH
		else:
			dir =  WEST
	else:
		dir = STILL
	
	target = map.getSite(location, dir)
	if site.strength <= target.strength:
		dir = STILL
	
	logger.debug("Chosen direction %s: %d" % (location, dir) )
	return dir

while True:
	moves = []
	logger.debug("****** PREP TURN %d ******" % turnCounter)
	gameMap = getFrame()
	turnCounter += 1
	logger.debug("****** START TURN %d ******" % turnCounter)
	logger.debug(gameMap)
	
	t = gameMap.getTerritory(myID)
	center = t.getCenter().getRealCenter()
	logger.debug("My center: \t%s" % str(t.getCenter().getRealCenter()))
	
	
	for y in range(gameMap.height):
		for x in range(gameMap.width):
			loc = Location(x,y)
			if gameMap.getSite(loc).owner == myID:
				dir = getDirForSquare(gameMap, loc)
				moves.append(Move(loc, dir))
				
					
	sendFrame(moves)
	gameMap.clearTerritories()
