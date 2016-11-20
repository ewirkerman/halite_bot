from hlteric import *
from networkingeric import *
import logging
from math import pi
from need import Need
from attack import Attack
import cProfile
import os


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


test_inputs = [
"1",
"3 3",
"1 2 3 4 5 6 7 8 9"
]

logger.info("Initialized logging")

def remove_sublist(main, sub):
	for m in sub:
		try:
			main.remove(m)
		except ValueError:
			pass

def evaluateSite(site):
	swing_factor = 1
	if type(site) == Location:
		site = gameMap.getSite(site)
	str = site.strength
	if str < 1:
		str = 1
	if len(site.enemies) > 0:
		swing_factor = 255
	return swing_factor*site.production/str

def getBestDir(map, location):
	bestDir = None
	bestValue = 0
	
	base = int(random.random()*4)
	dir_list = CARDINALS
	random.shuffle(dir_list)
	#logger.debug(dir_list)
	for dir in dir_list:
		site = map.getSite(location, dir)
		value = evaluateSite(site)
		if site.owner != myID and (not bestDir or bestValue < value):
#			logger.debug("Found new bestDir: %s" % dir)
			bestDir = dir
			bestValue = value
	return bestDir
	
def calcExpansionFactor():
	return 10

def getDirForSquare(map, location):
	t = map.getTerritory(myID)
	center = t.getCenter()
	angle = map.getAngle(center, location)
	deg = math.degrees(angle)
	
	#logger.debug("Angle from %s to %s: %d" % (center, location, deg))
	
	dir = STILL
	
	expansion_value = calcExpansionFactor()
	
	site = map.getSite(location)
	
	# frontier location
	if len(site.friends) < 4:
		dir = getBestDir(map, location)
		target = map.getSite(location, dir)
		if site.strength <= target.strength:
			dir = STILL
	
	# interior location who isn't ready yet
	elif site.strength < expansion_value * site.production:
		dir = STILL
	
	# move to adj frontier
	elif hasattr(site, "frontDir"):
		dir = site.frontDir
		
	elif True:
		target = None
		for terr in map.getTerritories():
			if terr.owner != myID:
				c = terr.getCenter()
				if not target or map.getDistance(location, c) < map.getDistance(location, target):
					target = c
		dir = map.getDirection(location, target)
	
	# highway to cardinals
	else:
		if t.isCenterRowFull():
			logger.debug("Row is full - splitting NS")
			if deg <= 0:
				dir = NORTH
			else:
				dir = SOUTH
				
		elif t.isCenterColumnFull():
			logger.debug("Col is full - splitting EW")
			if abs(deg) <= 90:
				dir = EAST
			else:
				dir = WEST
				
		else:
			if deg < 45 and deg > -45:
				if deg > 0:
					dir = NORTH
				elif deg < 0:
					dir =  SOUTH
				else:
					dir =  EAST
			elif deg >= 45 and deg < 135:
				if deg > 90:
					dir =  EAST
				elif deg < 90:
					dir =  WEST
				else:
					dir =  SOUTH
			elif deg <= -45 and deg > -135:
				if deg > -90:
					dir =  WEST
				elif deg < -90:
					dir =  EAST
				else:
					dir =  NORTH
			elif deg >= 135 or deg <= -135:
				if deg == 180:
					dir = WEST
				elif deg > 0:
					dir = NORTH
				elif deg < 0:
					dir = SOUTH
				else:
					dir = WEST
		target = map.getSite(location, dir)
		if site.strength + target.strength > 255 and target.strength > site.strength:
			dir = STILL
			
	target = map.getSite(location, dir)
	
	
	#logger.debug("Chosen direction %s: %d" % (location, dir) )
	return dir
	
#def liberate(gameMap, t, loc):
#	site = gameMap.getSite(loc)
#	strength = site.strength
#	
#	moves = []
#	for f in site.friends:
#		fsite = gameMap.getSite(f[0])
#		if f[0] in t.unmoved:
#			strength -= fsite.strength
#			logger.debug("Unmoved Friend %s!" % f[0])
#	
#	logger.debug("%s remaining strength" % strength)
#	if strength < 0:
#		for f in site.friends:
#			if f[0] in t.unmoved:
#				l = f[0]
#				logger.debug("Using %s -> %s!" % (f[0], f[1]))
#				t.unmoved.remove(l)
#				moves.append(Move(l, f[1]))
#	return moves
	


def getExpansiveDir(gameMap, loc):
	target = None
	for terr in gameMap.getTerritories():
		if terr.owner != myID:
			c = terr.getCenter()
			if not target or gameMap.getDistance(loc, c) < gameMap.getDistance(loc, target):
				target = c
	dir = gameMap.getDirection(loc, target)
	for d in CARDINALS:
		if gameMap.getSite(loc, dir).strength >= gameMap.getSite(loc).strength:
			dir = STILL
			break
	return dir

gameMap = None
contacted = False
def main():
	global turnCounter
	global gameMap
	moves = []
	logger.debug("****** PREP TURN %d ******" % turnCounter)
	gameMap = getFrame()
	turnCounter += 1
	logger.debug("****** START TURN %d ******" % turnCounter)
	
	t = gameMap.getTerritory(myID)
	center = t.getCenter()
	logger.debug(gameMap.mapToStr(t.getCenter()))
	#logger.debug("My center: \t%s" % str(t.getCenter().getRealCenter()))
	#logger.debug("My frontier: ")
	#for f in t.frontier:
	#	logger.debug(f)
	#logger.debug("My fringe: ")
	#for f in t.fringe:
	#	logger.debug(f)
	
	t.unmoved = copy.copy(t.territory)
	#logger.debug("Initial moves: %s" % t.unmoved)
	
	
	n = Attack(gameMap)
	mvs = n.get_moves(t.fringe, t.frontier, t.unmoved, turnCounter)
	t.unmoved -= set([m.loc for m in mvs])
	moves.extend(mvs)
	
	### This is the Need-based assist pattern
	sorted_fringe = sorted(t.fringe, key=evaluateSite)
	sorted_fringe.reverse()
	for loc in sorted_fringe:
		site = gameMap.getSite(loc)
		n = Need(site, gameMap)
		mvs = n.get_moves(t.unmoved)
			
		#if len(site.enemies) > 0:
		#	logger.debug("Near an enemy, so reverting to killbot")
		#	moves.clear()
		#	break
		t.unmoved -= set([m.loc for m in mvs])
		moves.extend(mvs)
		
		
	## Maybe we will let them go into the needs before they are ready if and only if they are adjacent to an emeny and then also make those squares
	# the first ones on the fringe and maybe inflate the strength of the Need so it pulls enough
	
	
	#unm = copy.copy(t.unmoved)
	#for loc in unm:
	#	t.unmoved.remove(loc)
	#	dir = getExpansiveDir(gameMap, loc)
	#	m = Move(loc, dir)
	#	moves.append(m)
	#	gameMap.updateMap(m)
	
	### This is the square expansion that I don't really care for
	#for loc in t.fringe:
	#	lib_moves = liberate(gameMap, t, loc)
	#	logger.debug("Remaining moves:")
	#	for u in t.unmoved:
	#		logger.debug(u)
	#	moves.extend(lib_moves)
	#	move_set = [move.loc for move in lib_moves]
	
	
	
	### This is the natural killbot code
	for loc in t.unmoved:
		#logger.debug("Activate Killbot!")
		dir = getDirForSquare(gameMap, loc)
		m = Move(loc, dir)
		moves.append(m)
		gameMap.updateMap(m)
				
					
	sendFrame(moves)
	gameMap.clearTerritories()

testBot()
		
		
myID, gameMap = getInit(getString)
sendInit("MyPythonBot")

turnCounter = 0

def main_loop():
	while True:
		main()
#		cProfile.run('main()', 'stats\mybot-turn%s.stats' % turnCounter)
#cProfile.run('main_loop()', 'stats\mybot.stats')
main_loop()