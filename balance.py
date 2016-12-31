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
	s = max([site.strength, 1]) ** 1.5
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
	elif not claim_move_conditions(claim_combo.parent):
		strength += claim_combo.parent.site.strength
		# logging.getLogger("bot").debug("stationary strength=%s"% strength)
	for claim in claim_combo:
		strength += claim.site.strength
		waste -= max([claim.site.strength + 2 * claim.site.production - 255, 0])
	# logging.getLogger("bot").debug("total strength=%s"% strength)
	
	if strength > 255:
		waste = strength - 255
		strength = 255
	# logging.getLogger("bot").debug("waste=%s"% waste)
	# logging.getLogger("bot").debug("strength=%s"% strength)
	
	if claim_combo.parent.is_capped() and claim_combo.parent.is_root():
		# if the combination doesn't actually solve the last layer, then spoil it by raising the strength
		# this is a min heap, so the less strength we take it with, the better
		if strength < 1:
			strength += 1024
		value = (strength + 4*waste)
	else:
		value = -1 * (strength - 4*waste)
	# logging.getLogger("bot").debug("value=%s"% value)
	return value

def uncapped_claim_benefit(claim):
	damage = 0
	for move in claim.site.enemies:
		site = move.loc.site
		damage += move.loc.site.strength
		
	
	if claim.root is claim:
		return .3*claim.gameMap.target_uncapped_value * (1 + damage/(1020*1000))
	else:
		return claim.root.benefit

	
	
def claim_combo_valid(claim_combo):
	return True
	
def claim_move_conditions(claim, parent = None):
	if not claim.get_parents():
		return False
	return claim_move_conditions_parentless(claim)

	
def claim_move_conditions_parentless(claim):
	#this needs to be locally decidable based on a child and its parent.  Right now it only looks at child and that's ok
	# for capped claims, we can assume the parents aren't moving. For uncapped, it needs to be above the production threshhold
	if claim.site.owner != claim.gameMap.playerTag:
		return False
	
	if claim.root.is_capped():
		return False
	
	
	if ((claim.loc.x % 2 == claim.loc.y % 2) == (claim.gameMap.turnCounter % 2 == 0)) and not claim.gen == 1:
		return False

	return claim.site.strength > claim.site.production*7
	
	
def claim_complete_conditions(claim, this_gen_str = 0, this_gen_production = 0):
	# logging.getLogger("bot").debug("Is %s + %s > %s? %s" % (claim.strength, this_gen_str, claim.cap, claim.strength + this_gen_str > claim.cap))
	return claim.strength + this_gen_str > claim.cap
