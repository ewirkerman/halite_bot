from hlt2 import *
from networking2 import *
from moves import *
import logging
attack_logger = logging.getLogger('bot')
base_formatter = logging.Formatter("%(asctime)s : %(levelname)s %(message)s")
log_file_name = 'bot.debug'
hdlr = logging.FileHandler(log_file_name)
hdlr.setFormatter(base_formatter)
hdlr.setLevel(logging.DEBUG)
attack_logger.setLevel(logging.DEBUG)




class Attack:
	def __init__(self,map):
		self.gameMap = map
		
	def is_satisfied(self):
		met = self.strength > self.site.strength
		attack_logger.debug("Help %s > Need %s? %s" %(self.strength, self.site.strength, met))
		return met
	
	def create_wave(self, wave, already_waved, frontier, past_frontier):
		next_wave = []
		attack_logger.info("Creating a wave from (past_frontier = %s):" % past_frontier)
		for move in wave:
			attack_logger.info("%s -> %s" % (move.loc, move.direction))
		attack_logger.debug("Excluding:")
		for l in already_waved:
			attack_logger.debug(l)
		
		
		found_internal = False
		for move in wave:
			attack_logger.debug("Getting friends of: %s" % move.loc)
			site = self.gameMap.getSite(move.loc)
			for friend_move in site.friends:
				attack_logger.debug("Checking friend of: %s" % friend_move.loc)
				fsite = self.gameMap.getSite(friend_move.loc)
				if not friend_move.loc in frontier:
					found_internal = True
				attack_logger.debug("str(%s) internal = %s, already = %s" % (fsite.strength,not friend_move.loc in frontier,friend_move.loc in already_waved) )
				if (not past_frontier or not friend_move.loc in frontier) and not friend_move.loc in already_waved:
					attack_logger.debug("Adding a Move: %s, %s" % (friend_move.loc, friend_move.direction))
					already_waved.add(friend_move.loc)
					next_wave.append(friend_move)
		
		for move in next_wave:
			attack_logger.info("%s -> %s" % (move.loc, move.direction))
		return next_wave, found_internal
		
	def get_moves(self, fringe, frontier, loc_pool, turn_count):
		waves = []
		already_waved = set()
		past_frontier = False
		seed = [f for f in fringe if self.gameMap.getSite(f).strength == 0]
		wave = []
		for loc in seed:
			site = self.gameMap.getSite(loc)
			for friend_move in site.friends:
				if not friend_move.loc in already_waved:
					already_waved.add(friend_move.loc)
					wave.append(friend_move)
				
		
		
		
		while (len(wave) > 1):
			new_wave, found_internal = self.create_wave(wave, already_waved, frontier, past_frontier)
			past_frontier = found_internal
			attack_logger.info("Appending a Wave")
			for move in new_wave:
				attack_logger.info("%s -> %s" % (move.loc, move.direction))
			waves.append(new_wave)
			wave = new_wave
		
		for i in range(len(waves)):
			attack_logger.info("Wave %s:" % i)
			attack_logger.info("%s" % waves[i])
			for move in waves[i]:
				attack_logger.info("%s -> %s" % (move.loc, move.direction))
				
		
		freq = 3
		i = 0
		moves = []
		for i in range(len(waves)):
			attack_logger.debug("Sending wave %s:" % i)
			for move in waves[i]:
				site = self.gameMap.getSite(move.loc)
				if site.strength == 255:
					moves.append(move)
				elif site.strength > site.production * 10:
					moves.append(move)
					#for friend_move in site.friends:
					#	if self.gameMap.getSite(friend_move.loc).strength == 0:
					#		moves.append(move)
					#		break
			#moves.extend([Move(move.loc, move.direction) for t in waves[i] if self.gameMap.getSite(move.loc).strength > 0 and any([self.gameMap.getSite(move.loc).strength > 0])])
			#if (i + turn_count) % freq == 0:
			#	
			#else:
			#	attack_logger.debug("Holding wave %s:" % i)
			#	moves.extend([Move(move.loc, STILL) for t in waves[i]])
		
		for move in moves:
			attack_logger.debug(move)
		return moves