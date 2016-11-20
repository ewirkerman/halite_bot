from hlteric import *
from networkingeric import *
import logging
attack_logger = logging.getLogger('bot')
base_formatter = logging.Formatter("%(asctime)s : %(levelname)s %(message)s")
log_file_name = 'bot.debug'
hdlr = logging.FileHandler(log_file_name)
hdlr.setFormatter(base_formatter)
hdlr.setLevel(logging.DEBUG)
attack_logger.setLevel(logging.ERROR)




class Attack:
	def __init__(self,map):
		self.gameMap = map
		
	def is_satisfied(self):
		met = self.strength > self.site.strength
#		#attack_logger.debug("Help %s > Need %s? %s" %(self.strength, self.site.strength, met))
		return met
	
	def create_wave(self, wave, already_waved, frontier, past_frontier):
		next_wave = []
#		attack_logger.info("Creating a wave from (past_frontier = %s):" % past_frontier)
#		for l in wave:
#			attack_logger.info("%s -> %s" % (l[0], l[1]))
#		attack_logger.debug("Excluding:")
#		for l in already_waved:
#			attack_logger.debug(l)
		
		
		found_internal = False
		for loc in wave:
#			attack_logger.debug("Getting friends of: %s" % loc[0])
			site = self.gameMap.getSite(loc[0])
			for friend in site.friends:
#				attack_logger.debug("Checking friend of: %s" % friend[0])
				fsite = self.gameMap.getSite(friend[0])
				if not friend[0] in frontier:
					found_internal = True
#				attack_logger.debug("str(%s) internal = %s, already = %s" % (fsite.strength,not friend[0] in frontier,friend[0] in already_waved) )
				if (not past_frontier or not friend[0] in frontier) and not friend[0] in already_waved:
#					logger.debug("Adding a Move: %s, %s" % (friend[0], friend[1]))
					already_waved.add(friend[0])
					next_wave.append(friend)
		
#		for t in next_wave:
#			attack_logger.info("%s -> %s" % (t[0], t[1]))
		return next_wave, found_internal
		
	def get_moves(self, fringe, frontier, loc_pool, turn_count):
		waves = []
		already_waved = set()
		past_frontier = False
		seed = [f for f in fringe if len(self.gameMap.getSite(f).enemies) > 0]
		wave = []
		for loc in seed:
			site = self.gameMap.getSite(loc)
			for friend in site.friends:
				if not friend[0] in already_waved:
					already_waved.add(friend[0])
					wave.append(friend)
				
		
		
		
		while (len(wave) > 1):
			new_wave, found_internal = self.create_wave(wave, already_waved, frontier, past_frontier)
			past_frontier = found_internal
##			attack_logger.info("Appending a Wave")
#			for t in new_wave:
#				attack_logger.info("%s -> %s" % (t[0], t[1]))
			waves.append(new_wave)
			wave = new_wave
		
#		for i in range(len(waves)):
#			attack_logger.info("Wave %s:" % i)
#			attack_logger.info("%s" % waves[i])
#			for t in waves[i]:
#				attack_logger.info("%s -> %s" % (t[0], t[1]))
				
		
		freq = 3
		i = 0
		moves = []
		for i in range(len(waves)):
#			attack_logger.debug("Sending wave %s:" % i)
			for t in waves[i]:
				site = self.gameMap.getSite(t[0])
				if site.strength == 255:
					moves.append(Move(t[0], t[1]))
				elif site.strength > site.production * 10:
					for friend in site.friends:
						if self.gameMap.getSite(friend[0]).strength == 0:
							moves.append(Move(t[0], t[1]))
							break
			#moves.extend([Move(t[0], t[1]) for t in waves[i] if self.gameMap.getSite(t[0]).strength > 0 and any([self.gameMap.getSite(t[0]).strength > 0])])
			#if (i + turn_count) % freq == 0:
			#	
			#else:
#			#	attack_logger.debug("Holding wave %s:" % i)
			#	moves.extend([Move(t[0], STILL) for t in waves[i]])
		
#		for move in moves:
#			logger.debug(move)
		return moves