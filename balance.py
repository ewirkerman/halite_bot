from util import *
from hlt2 import Location
import logging
	
theMap = None
def evaluateMapSite(myMap):
	global theMap
	theMap = myMap
	return evaluateSite
	
def evalSiteProduction(site, claim = None):
	p = site.production
	
	if site.enemies:
		p += sum([min([move.loc.site.strength, site.strength]) for move in site.enemies])
	return p
	
def evalSiteStrength(site):
	# should cache the answer of this
	s = max([site.strength, 1]) ** 1
	return s

def claim_combo__lt__(self, other):
	return self.value < other.value
	
def evaluate_claim_combo(claim_combo):
	# This should include a provision that minimizes the amount of production lost, minimizes the amount of overkill
	# # logging.getLogger("bot").debug("Checking value parent %s of claim_combo : %s" % (claim_combo.parent, debug_list(claim_combo.claims)) )
	
	strength = 0
	waste = 0
	if claim_combo.parent.is_root():
		strength -= claim_combo.parent.site.strength
		#logging.getLogger("bot").debug("root strength=%s"% strength)
	else:
		#logging.getLogger("bot").debug("stationary strength=%s"% strength)
		if not claim_move_conditions(claim_combo.parent):
			strength += claim_combo.parent.site.strength + claim_combo.parent.site.production
		pass
	for claim in claim_combo:
		strength += claim.site.strength
		waste -= max([claim.site.strength + 2 * claim.site.production - 255, 0])
	# logging.getLogger("bot").debug("total strength=%s"% strength)
	
	if strength > 255:
		waste = strength - 255
		strength = 255
	# logging.getLogger("bot").debug("waste=%s"% waste)
	# logging.getLogger("bot").debug("strength=%s"% strength)
	
	waste_avoidance = 4
	
	if claim_combo.parent.is_capped() and claim_combo.parent.is_root() and claim_combo.parent.site.strength > 0:
		# if the combination doesn't actually solve the last layer, then spoil it by raising the strength
		# this is a min heap, so the less strength we take it with, the better
		if strength < 1:
			strength += 1024
		value = (strength + waste_avoidance*waste)
	else:
		value = -1 * (strength - waste_avoidance*waste)
	# logging.getLogger("bot").debug("value=%s"% value)
	return value

def strength_limit(site):
	return 255
	
def uncapped_claim_benefit(claim):
	damage = 0
	for move in claim.site.enemies:
		site = move.loc.site
		damage += move.loc.site.strength
		
	
	if claim.root is claim:
		return 1*claim.gameMap.target_uncapped_value * (1 + damage/(1020*1000))
	else:
		return claim.root.benefit

	
	
def claim_combo_valid(claim_combo):
	return True
	
def claim_move_conditions(claim, parent = None):
	if not claim.get_parents():
		return False
	return claim_move_conditions_parentless(claim)

def claim_move_conditions_parentless(claim):
	
	
	# Never move a tile you don't own
	if claim.site.owner != claim.gameMap.playerTag or claim.site.strength == 0:
		return False
		
	# raise Exception("#will move, vs. won't move but isn't going to anyone else vs. will go to someone else")	
	if claim.root.is_capped():
		return claim.gen == claim.root.max_gen and claim_complete_conditions(claim.root)
		
		
	else: # UNCAPPED
		if claim.gen == 1 and claim.root.site.strength > 0:
			return False
		else:
			return claim.site.strength > claim.site.production*7

	# Uncapped requirement for MOVE
	
	
def claim_complete_conditions(claim, this_gen_str = 0, this_gen_production = 0):
	# logging.getLogger("bot").debug("Is %s + %s > %s? %s" % (claim.strength, this_gen_str, claim.cap, claim.strength + this_gen_str > claim.cap))
	return claim.is_capped() and claim.strength + this_gen_str > claim.cap
