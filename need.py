from hlt2 import *
from networking2 import *
from moves import *
import logging

need_logger = logging.getLogger('need')
base_formatter = logging.Formatter("%(asctime)s : %(levelname)s %(message)s")
log_file_name = 'bot.debug'
hdlr = logging.FileHandler(log_file_name)
hdlr.setFormatter(base_formatter)
hdlr.setLevel(logging.DEBUG)
need_logger.addHandler(hdlr)
need_logger.setLevel(logging.ERROR)

import copy

class NeedError(Exception):
	pass



class Need:
	def __init__(self, site, map):
		self.gameMap = map
		self.site = site
		self.production = 0
		self.strength = 0
		need_logger.debug("Need %s for %s at %s" % (site.strength, site.production,site.loc))
		
	def is_satisfied(self):
		met = self.strength > self.site.strength
		need_logger.debug("Help %s > Need %s? %s" %(self.strength, self.site.strength, met))
		return met
	
	def check_generation(self, generation, already_used, loc_pool):
		next_gen = []
		this_gen = []
		met = None
		need_logger.debug("Already used: %s" % debug_list(already_used) )
		need_logger.debug("Generation: %s" % debug_list(generation))
		for move in generation:
			site = self.gameMap.getSite(move.loc)
			self.apply_help(move.loc, site)
			this_gen.append(move)
			
			for neutral_move in site.neutrals:
				nsite = self.gameMap.getSite(neutral_move.loc)
				if nsite.strength == 0 and self.site.strength > 0:
					need_logger.debug("Aborting the Need for %s because of a front at %s" % (self.site.loc, nsite.loc))
					raise NeedError("Aborting the Need for %s because of a front at %s" % (self.site.loc, nsite.loc ))
			for friend_move in site.friends:
				if not friend_move.loc in [used.loc for used in already_used] and not friend_move.loc in [used.loc for used in next_gen] and friend_move.loc in loc_pool:
					next_gen.append(friend_move)
			met = self.is_satisfied()
			if met:
				break
		return met, this_gen, next_gen
		
		
	def get_moves(self, loc_pool):
		gen = []
		already_used = []
		
		need_logger.debug("Seeding from : %s" % debug_list(self.site.friends) )
		# This sets up the base generation from the location we are targeting
		for friend_move in self.site.friends:
			if not friend_move.loc in [used.loc for used in already_used] and not friend_move.loc in [used.loc for used in gen] and friend_move.loc in loc_pool:
				gen.append(friend_move)
		
		need_logger.debug("Seed gen: %s" % debug_list(gen) )
		need_logger.debug("Loc Pool: %s" % debug_list(loc_pool) )
		while len(gen) > 0:
			satisfied, this_gen, next_gen = self.check_generation(gen, already_used, loc_pool)
			first = False
			if satisfied:
				need_logger.debug("Satisfied! %s" % debug_list(this_gen))
				return [Move(m.loc, STILL) for m in already_used] + this_gen
			else:
				need_logger.debug("Mid gen: %s" % debug_list(this_gen))
				already_used.extend(this_gen)
				need_logger.debug("Already_used list: %s" % debug_list(already_used))
				self.strength += self.production
				#if self.is_satisfied():
				#	return [Move(m.loc, STILL) for m in already_used]
				gen = next_gen
		return [Move(m.loc, STILL) for m in already_used]
		
	def apply_help(self, loc, site):
		need_logger.debug("Pledged %s from %s" % (site.strength,loc))
		
		self.production += site.production
		self.strength += site.strength
		