from hlteric import *
from networkingeric import *
import logging
need_logger = logging.getLogger('need')
base_formatter = logging.Formatter("%(asctime)s : %(levelname)s %(message)s")
log_file_name = 'bot.debug'
hdlr = logging.FileHandler(log_file_name)
hdlr.setFormatter(base_formatter)
hdlr.setLevel(logging.DEBUG)
need_logger.addHandler(hdlr)
need_logger.setLevel(logging.DEBUG)
import copy



class Need:
	def __init__(self, site, map):
		self.gameMap = map
		self.site = site
		self.production = 0
		self.strength = 0
#		need_logger.debug("Need %s for %s at %s" % (site.strength, site.production,site.loc))
		
	def is_satisfied(self):
		met = self.strength > self.site.strength
#		need_logger.debug("Help %s > Need %s? %s" %(self.strength, self.site.strength, met))
		return met
	
	def check_generation(self, generation, already_used, loc_pool):
		next_gen = []
		this_gen = []
		d = dict(generation)
		met = None
#		need_logger.debug("Already used: %s" % already_used)
#		need_logger.debug("Generation: %s" % d)
		for loc, dir in generation:
			site = self.gameMap.getSite(loc)
			self.apply_help(loc, site)
			this_gen.append((loc, dir))
			
			for f in site.friends:
				if not f[0] in [used[0] for used in already_used] and f[0] in loc_pool:
					next_gen.append(f)
			met = self.is_satisfied()
			if met:
				break
		return met, this_gen, next_gen
		
		
	def get_moves(self, loc_pool):
		gen = [f for f in self.site.friends if f[0] in loc_pool]
		first_gen = copy.copy(gen)
		
#		need_logger.debug("Loc Pool: %s" % loc_pool)
		already_used = []
		while len(gen) > 0:
			satisfied, this_gen, next_gen = self.check_generation(gen, already_used, loc_pool)
			first = False
			if satisfied:
#				need_logger.debug("Can capture!, using moves")
#				need_logger.debug("Used up moves:")
#				for m in already_used:
##					need_logger.debug("%s->%s" % (m[0], STILL))
#				for m in this_gen:
#					need_logger.debug("%s->%s" % (m[0], m[1]))
				return [Move(m[0], STILL) for m in already_used] + [Move(m[0],m[1]) for m in this_gen]
			else:
				already_used.extend(this_gen)
				self.strength += self.production
				gen = next_gen
		return [Move(m[0], STILL) for m in already_used]
		
	def apply_help(self, loc, site):
#		need_logger.debug("Maybe lending %s from %s" % (site.strength,loc))
		
		self.production += site.production
		self.strength += site.strength
		