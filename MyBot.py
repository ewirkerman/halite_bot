from hlt2 import *
from networking2 import *
from moves import *
import logging
import time
from math import pi
from need import *
from attack import Attack
import cProfile
import pstats
import os

all
##### Logging Setup
import logging
logger = logging.getLogger('bot')

base_formatter = logging.Formatter("%(asctime)s : %(levelname)s %(message)s")
log_file_name = 'bot.debug'
hdlr = logging.FileHandler(log_file_name)
hdlr.setFormatter(base_formatter)
hdlr.setLevel(logging.DEBUG)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)	


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
	return swing_factor*site.production/(str*str)
	
### when total production is low, should be favor sites with lower strenght
### when total production is high, should be favor sites with higher production
	
	

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

	
def findFronts(t, mf):
	logger.debug("Attacking fronts")

	fronts = [f for f in t.fringe if gameMap.getSite(f).strength == 0]
	if len(fronts) == 0:
		fronts = t.fringe
	
	n = Attack(gameMap)
	return n.get_moves(fronts, [], mf.get_unused_moves(), turnCounter)
	
	
	
def addressNeeds(needy_locations, mf, need_limit = 100):
	### This is the Need-based assist pattern
	logger.debug("Finding needs")
	
	needs = []
	try:
		for loc in needy_locations[:]:
			site = gameMap.getSite(loc)
			n = Need(site, gameMap, mf.get_unused_moves())
			needs.append(n)
			moves = n.get_moves()
			if len(moves) < need_limit:
				mf.submit_moves(moves)
	except NeedError:
		pass
	
	logger.debug("Need Map (%s and shorter): %s" % (need_limit, getMoveMap([item for sublist in needs for item in sublist.moves])))

	
gameMap = None
contacted = False
attackCenters = None
def main():
	clock = time.clock()
	global turnCounter
	global gameMap
	global attackCenters
	
	turnCounter += 1
	logger.debug("****** PREP TURN %d ******" % turnCounter)
	gameMap = getFrame()
	gameMap.lastAttackCenters = attackCenters
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
	
	#logger.debug("Initial moves: %s" % t.unmoved)
	mf = MoveFork(gameMap, t.territory)
	
	needy_locations = sorted(t.fringe, key=evaluateSite)
	needy_locations.reverse()
	
	
	early_moves, late_moves = findFronts(t, mf)
	logger.debug("Early 	Attack Map: " + getMoveMap(early_moves))
	mf.submit_moves(early_moves)
	
	addressNeeds(needy_locations, mf)
	
	logger.debug("Late Attack Map: " + getMoveMap(late_moves))
	mf.submit_moves(late_moves, weak=True)
	
	
	
	
	
	
	
	

	
	#logger.debug("Need map: " + getMoveMap(mf.move_list))
	#logger.debug("Remaining moves: %s" % debug_list(mf.get_unused_moves()))
	
	attackCenters = gameMap.attackCenters 

					
	mf.output_all_moves()
	gameMap.clearTerritories()
	logger.debug("****** END TURN %d (time=%s) ******" % (turnCounter,time.clock()-clock))

testBot()
		
		
try:
	myID, gameMap = getInit(getString)
except Exception as e:
	with open("bot.debug", "a") as f:
		f.write(e)
sendInit("MyPythonBot")

turnCounter = -1

def main_loop():
	while True:
		main()
		#fname = 'stats\mybot-turn%s.stats' % turnCounter
		#cProfile.run('main()', fname)
		#stream = open(log_file_name, 'a');
		#stats = pstats.Stats(fname, stream=stream)
		#stats.sort_stats("time").print_stats()
cProfile.run('main_loop()', 'stats\mybot.stats')
main_loop()