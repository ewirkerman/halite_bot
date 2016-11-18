from hlteric import *
from networkingeric import *
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

def remove_sublist(main, sub):
	for m in sub:
		try:
			main.remove(m)
		except ValueError:
			pass

def evaluateSite(site):
	if type(site) == Location:
		site = gameMap.getSite(site)
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
				if not target or map.getDistance(center, c) < map.getDistance(center, target):
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
	
def liberate(gameMap, t, loc):
	site = gameMap.getSite(loc)
	strength = site.strength
	
	moves = []
	for f in site.friends:
		fsite = gameMap.getSite(f[0])
		if f[0] in t.unmoved:
			strength -= fsite.strength
			logger.debug("Unmoved Friend %s!" % f[0])
	
	logger.debug("%s remaining strength" % strength)
	if strength < 0:
		for f in site.friends:
			if f[0] in t.unmoved:
				l = f[0]
				logger.debug("Using %s -> %s!" % (f[0], f[1]))
				t.unmoved.remove(l)
				moves.append(Move(l, f[1]))
	return moves
	
class Need:
	def __init__(self, location):
		self.production = 0
		self.strength = 0
		self.site = gameMap.getSite(location)
		logger.debug("Need %s for %s at %s" % (self.site.strength, self.site.production,location))
		
	def is_satisfied(self):
		met = self.strength > self.site.strength
		logger.debug("Help %s > Need %s? %s" %(self.strength, self.site.strength, met))
		return met
	
	def check_generation(self, generation, already_used, loc_pool):
		next_gen = []
		this_gen = []
		d = dict(generation)
		met = None
		logger.debug("Already used: %s" % already_used)
		logger.debug("Generation: %s" % d)
		for loc, dir in generation:
			site = gameMap.getSite(loc)
			self.apply_help(loc, site)
			this_gen.append((loc, dir))
			
			#next_gen.extend([f for f in site.friends if f[0] not in already_used and f[0] in loc_pool])
			for f in site.friends:
				if not f[0] in [used[0] for used in already_used] and f[0] in loc_pool:
					next_gen.append(f)
			met = self.is_satisfied()
			if met:
				break
		return met, this_gen, next_gen
		
		
	def get_moves(self, loc_pool):
		gen = [f for f in self.site.friends if f[0] in loc_pool]
		
		logger.debug("Loc Poo: %s" % loc_pool)
		already_used = []
		while len(gen) > 0:
			satisfied, this_gen, next_gen = self.check_generation(gen, already_used, loc_pool)
			if satisfied:
				logger.debug("Can capture!, using moves")
				logger.debug("Used up moves:")
				for m in already_used:
					logger.debug("%s->%s" % (m[0], STILL))
				for m in this_gen:
					logger.debug("%s->%s" % (m[0], m[1]))
				return [Move(m[0], STILL) for m in already_used] + [Move(m[0],m[1]) for m in this_gen]
			else:
				already_used.extend(this_gen)
				self.strength += self.production
				gen = next_gen
		
		return [Move(m[0], STILL) for m in already_used]
		
	def apply_help(self, loc, site):
		logger.debug("Maybe lending %s from %s" % (site.strength,loc))
		self.production += site.production
		self.strength += site.strength
		
	

gameMap = None
def main():
	global turnCounter
	global gameMap
	while True:
		moves = []
		logger.debug("****** PREP TURN %d ******" % turnCounter)
		gameMap = getFrame()
		turnCounter += 1
		logger.debug("****** START TURN %d ******" % turnCounter)
		
		t = gameMap.getTerritory(myID)
		center = t.getCenter().getRealCenter()
		logger.debug(gameMap.mapToStr(t.getCenter()))
		logger.debug("My center: \t%s" % str(t.getCenter().getRealCenter()))
		logger.debug("My frontier: ")
		for f in t.frontier:
			logger.debug(f)
		logger.debug("My fringe: ")
		for f in t.fringe:
			logger.debug(f)
		
		t.unmoved = copy.copy(t.territory)
		logger.debug("Initial moves: %s" % t.unmoved)
		
		
		### This is the Need-based assist pattern
		sorted_fringe = sorted(t.fringe, key=evaluateSite)
		sorted_fringe.reverse()
		for loc in sorted_fringe:
			n = Need(loc)
			mvs = n.get_moves(t.unmoved)
			t.unmoved -= set([m.loc for m in mvs])
			#for m in mvs:
			#	t.unmoved.remove(m.loc)
			#	logger.debug("Used move: %s" % m)
			moves.extend(mvs)
		
		
		
		
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
			dir = getDirForSquare(gameMap, loc)
			m = Move(loc, dir)
			moves.append(m)
			gameMap.updateMap(m)
					
						
		sendFrame(moves)
		gameMap.clearTerritories()

myID, gameMap = getInit()
sendInit("MyPythonBot")

turnCounter = 0

import cProfile
cProfile.run('main()', 'mybot.stats')	

