from util import *
from hlt2 import Location
import logging

def getAggressionFactor(gameMap, site):
	t = gameMap.getTerritory()
	#if 2*len(t.frontier) > len(t.territory):
	#	return 7#random.randint(3,7)
	return 5 #SpreadBot	
	
def getSplitWave(gameMap, waves):
	t = gameMap.getTerritory()
	#if 2*len(t.frontier) > len(t.territory):
	#	return len(waves) - 1

	if t.strength < t.production * 3:
		return 1
	return len(waves)/ 2 #SpreadBot	
	
def getSpreadWave(waves):
	return 2
	
theMap = None
def evaluateMapSite(myMap):
	global theMap
	theMap = myMap
	return evaluateSite


def evaluateSite(site):
	t = theMap.getTerritory()
	e_factor = 1
	if type(site) == Location:
		site = theMap.getSite(site)
	str = site.local_strength
	if str < 1:
		str = 1
	enemies = len(site.enemies)
	if enemies and not site.strength:
		e_factor = 255**(enemies*4 - len(site.friends) )
	#return swing_factor*site.local_production/(str**1.1)
	if t.fronts:
		return e_factor*site.local_production/(str**1.5)
	else:
		return e_factor*site.local_production/(str)#SpreadBot
		
def evaluateNeed(need):
	site = need.site
	t = theMap.getTerritory()
	e_factor = 1
	if type(site) == Location:
		site = theMap.getSite(site)
	str = site.local_strength
	if str < 1:
		str = 1
	enemies = len(site.enemies)
	if enemies and not site.strength:
		e_factor = 255**(enemies*4 - len(site.friends) )
	logging.getLogger("need").debug("production consumed for need at %s: %s" % (site.loc, need.production))
	return e_factor*site.local_production/(str+need.production)#SpreadBot
	return e_factor*site.local_production/(str)#SpreadBot

def evaluate_claim_combo(claim_combo):
	# This should include a provision that minimizes the amount of production lost, minimizes the amount of overkill
	return claim_combo.strength
	
def claim_combo_valid(claim):
	return True
	
def claim_move_conditions(claim):
	return True
	
def claim_complete_conditions(claim, this_gen_str = 0, this_gen_production = 0):
	
	logging.getLogger("bot").debug("Is %s + %s > %s? %s" % (claim.strength, this_gen_str, claim.cap, claim.strength + this_gen_str > claim.cap))
	return claim.strength + this_gen_str > claim.cap
	
def getNeedLimit():
	return 100 #SpreadBot	
	
def checkerOn():
	return True #SpreadBot	
	
def strength_limit(site):
	return 255#SpreadBot
	
def soft_strength_limit(site):
	return 255