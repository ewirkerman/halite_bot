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
	
	loss_avoidance = 10
	strength = 0
	loss = 0
	p_loss = 0
	if claim_combo.parent.site.owner == 0:
		strength -= claim_combo.parent.site.strength
		#logging.getLogger("bot").debug("root strength=%s"% strength)
	else:
		if not claim_combo.parent.will_move():
			strength += claim_combo.parent.site.strength + claim_combo.parent.site.production
			#logging.getLogger("bot").debug("stationary strength=%s"% strength)
			pass
	for claim in claim_combo:
		strength += claim.site.strength
		if claim.site.strength + claim.site.production > 255:
			p_loss -= claim.site.strength + claim.site.production - 255
		p_loss += claim.site.production
	# logging.getLogger("bot").debug("total strength=%s"% strength)
	
	if strength > 255:
		loss = strength - 255
		strength = 255
	# logging.getLogger("bot").debug("loss=%s"% loss)
	# logging.getLogger("bot").debug("strength=%s"% strength)
	
	e_str = claim_combo.parent.gameMap.get_enemy_strength(claim_combo.parent.loc)
	damage = 0	
	if e_str:
		damage = claim_combo.parent.gameMap.get_enemy_strength(claim_combo.parent.loc, damage_dealable=True)
	
	
	all_capped = all([claim.is_capped() for claim in claim_combo.claims])
	
	
	# We are away from the enemy so the less strength we take it with, the better
	if claim_combo.parent.is_capped() and claim_combo.parent.is_root() and not e_str and all_capped:
		
		# if you don't have enough strenght to take a strong neutral, this isn't a good combo
		if strength < 1 and claim_combo.parent.site.strength > 1:
			strength += 1024
		value = (strength + loss_avoidance*loss)
		## This bit just says don't move more than one 0 to get a zero, but now that I factor production lost in, this should be naturally prevented
		# elif strength < 1 and claim_combo.parent.site.strength < 1 and len(claim_combo) != 1:
			# strength += 1024
		
		# as few capped claims as possible and as much uncapped as possible
		
	else:
		value = -1 * (strength + damage - loss_avoidance*loss - p_loss)
	logging.getLogger("bot").debug("Claim combo from %s has %s" % (debug_list(claim_combo.claims), value) )
	return value
	
	

def strength_limit(site):
	return 255
	
def uncapped_claim_benefit(claim):
	damage = 0
	for move in claim.site.enemies:
		site = move.loc.site
		damage += move.loc.site.strength
		
	
	if claim.root is claim:
		return (1+claim.site.production/20)*claim.gameMap.target_uncapped_value * (1 + damage/(1020*1000))
	else:
		return claim.root.benefit

	
	
def claim_combo_valid(claim_combo):
	return True
	
def claim_move_conditions(claim, parent = None):
	if not claim.get_parent():
		return False
	return claim_move_conditions_parentless(claim)

def claim_move_conditions_parentless(claim):
	if claim.loc.site.heap.dir:
		return True
	
	enemy_str = 0
	parent = claim.get_parent()
	# Never move a tile you don't own
	if claim.site.owner != claim.gameMap.playerTag:
		ret = False

	elif claim.root.is_capped():
		ret = claim.gen == claim.root.max_gen and claim_complete_conditions(claim.root)
		
		
	else: # UNCAPPED
		if claim.gen == 1 and claim.root.site.strength > 0:
			ret = False
		else:
			# This I feel is a hack because I should just be able to count the incoming strength and beat it
			# ret = claim.site.strength > claim.site.production*7
			ret = True

	# logging.getLogger("bot").debug("Will %s (parent: %s) move (e_str = %s)? %s" % (claim, parent, enemy_str, ret) )
	return ret
	# Uncapped requirement for MOVE
	
	
def claim_complete_conditions(claim, this_gen_str = 0, this_gen_production = 0):
	if claim.ancestors < 1:
		# logging.getLogger("bot").debug("%s has no ancestors" % claim)
		return False
		
	if not claim.is_capped():
		# logging.getLogger("bot").debug("%s is not capped" % claim)
		return False
		
	if claim.strength + this_gen_str > claim.cap:
		# logging.getLogger("bot").debug("%s has enough to cover cap %s " % (claim, claim.cap) )
		return True
		
	if claim.strength < 1 and claim.cap < 1:
		# logging.getLogger("bot").debug("%s has 0 and needs 0" % (claim) )
		return True
	# logging.getLogger("bot").debug("%s will spread further" % (claim) )
	return False
