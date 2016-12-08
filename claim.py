from hlt2 import *
from networking2 import *
from moves import *
import logging
import heapq
import util
import itertools

attack_logger = logging.getLogger('attack')
base_formatter = logging.Formatter("%(levelname)s %(message)s")
log_file_name = 'bot.debug'
hdlr = logging.FileHandler(log_file_name)
hdlr.setFormatter(base_formatter)
hdlr.setLevel(logging.DEBUG)
attack_logger.setLevel(logging.ERROR)


def getStrFromMoveLoc(move):
	return move.loc.site.strength

class ClaimHeap:
	def __init__(self, site):
		self.heap = []
		self.site = site
		site.heap = self
		
	def add_claim(self, claim):
		logger.debug("Is %s in %s? %s" % (claim, debug_list(self.heap), claim in self.heap))
		for c in set(self.heap):
			if c.root is claim.root:
				logger.debug("Matched a root claim %s with %s" % (claim.root,c))
				if claim.gen < c.gen:
					logger.debug("%s had a higher gen than %s " % (c, claim))
					self.remove_claim(c)
				else:
					logger.debug("%s had a higher gen than %s " % (claim, c ))
					claim.parent.deactivate_child(claim)
		if not claim in self.heap:
			old_best = self.get_best_claim()
			heapq.heappush(self.heap, (claim))
			# Once a claim in in a heap, you can reference the heap with simply claim.heap
			claim.heap = self
			logger.debug("Added the claim %s to %s" % (claim, self.site.loc))
			self.check_heap(old_best)
		
	def remove_claim(self, claim):
		old_best = self.get_best_claim()
		self.heap = [c for c in self.heap if c is not claim]
		heapq.heapify(self.heap)
		claim.heap = None
		logger.debug("Removed the claim %s from %s" % (claim, self.site.loc))
		self.check_heap(old_best)
		
	def check_heap(self, old_best):
		new_best = self.get_best_claim()
		# if the best changes, then cancel the old best and issue the new best
		if old_best is not new_best:
			if old_best:
				logger.debug("Unspread the claim on %s from %s" % (old_best, old_best.parent))
				old_best.unspread()
				old_best.root.remove_gen(old_best)
				raise Error("This needs to allow the previous root to expand again because we nabbed a tile he thought he had")
			if new_best:
				if new_best.root.add_gen(new_best):
					logger.debug("Spreading new best claim on %s from %s" % (new_best, new_best.parent))
					new_best.spread()
				else:
					new_best.parent.deactivate_child(new_best)
		
	def get_best_claim(self):
		if self.heap:
			return self.heap[0]
		return None
		
class ClaimCombo:
	def __init__(self, parent, combo):
		self.parent = parent
		self.production = 0
		self.strength = 0
		self.claims = combo
		for c in combo:
			self.strength += c.strength
			self.production += c.production
		if not balance.claim_combo_valid(self):
			raise ValueError("Invalid combination of locations")
		self.value = balance.evaluate_claim_combo(self)
		
	def __lt__(self, other):
		return self.value < other.value

class Gen:
	def __init__(self, claims = []):
		self.claims = set(claims)
		self.production = 0
		self.strength = 0
		
	def __iter__(self):
		return self.claims.__iter__()
	
	def add(self, child):
		self.claims.add(child)
		self.production += child.production
		self.strength += child.strength
	
	def remove(self, child):
		self.claims.remove(child)
		self.production -= child.production
		self.strength -= child.strength

class Claim:
	def __init__(self, map, location, parent = None, dir=0, root = None):
		self.gameMap = map
		self.directionToParent = dir
		self.cap = 0
		self.heap = None
		if location.site.strength > 0: 
			self.cap = location.site.strength
		self.parent = parent or self
		self.loc = location
		self.site = self.loc.site
		self.root = root or self
		self.value = 0
		self.gen = 0
		self.max_gen = 0
		self.gens = {}
		if parent:
			self.gen = parent.gen + 1
		self.strength = 0
		self.production = 0
		if self.root is self:
			logger.debug("Creating a seed claim at %s"  % self.loc)
			self.value = balance.evaluateMapSite(map)(self.site)
			self.gens[0] = Gen([self])
			self.gens[0].production = 0
			self.gens[0].strength = 0
		else:
			self.strength = self.site.strength
			self.production = self.site.production
			self.value = self.root.value
		self.potential_children = set()
		self.active_children = set()
	
	def trigger(self):
		while not met:
			wait
			if not met:
				spread a full gen at a time, combining directional indifferences
	
	def get_total_production(self):
		p = 0
		for i in range(self.max_gen+1):
			logger.debug("Adding %s production to %s because gen %s waiting" % (self.gens[i].production,self.strength, i))
			p += self.gens[i].production
		return p
		
	def unspread(self):
		#rescind all children
		for child in set(self.active_children):
			child.unspread()
			self.deactivate_child(child)
		
	def is_top_claim(self):
		best = self.heap.get_best_claim()
		logger.debug("Top: %s vs %s" % (best, self))
		return best is self
		
	def add_gen(self, child):
		self.gens.setdefault(child.gen, Gen())
		logger.debug("Adding %s of gen %s to root %s (max_gen: %s - %s)" % (child,child.gen,self, self.max_gen, debug_list(self.gens[child.gen].claims)))
		while child.gen > self.max_gen:
			for i in range(self.max_gen+1):
				logger.debug("Adding %s production to %s because gen %s waiting" % (self.gens[i].production,self.strength, i))
				self.strength += self.gens[i].production
			self.max_gen += 1
		if True or not balance.claim_complete_conditions(self): 
			self.strength += child.strength
			self.gens[child.gen].add(child)
			logger.debug("Added %s with str %s, root now at %s" % (child,child.strength,self.strength))
			return True
		logger.debug("Didn't add %s with str %s because waiting works just as well" % (child,child.strength))
		return False
		
	def remove_gen(self, child):
		logger.debug("Removing %s of gen %s from root %s (max_gen: %s - %s)" % (child,child.gen,self, self.max_gen, debug_list(self.gens[child.gen].claims)))
		self.strength -= child.strength
		if child in self.gens[child.gen]:
			self.gens[child.gen].remove(child)
		else:
			logger.debug("Actually we never added him because waiting was easier")
			pass
		while child.gen < self.max_gen:
			for i in range(self.max_gen+1):
				logger.debug("Adding %s production to %s because gen %s waiting" % (self.gens[i].production,self.strength, i))
				self.strength -= self.gens[i].production
			self.max_gen -= 1
			self.max_gen = child.gen
		
	def deactivate_child(self, child):
		logger.debug("Deactivating %s" % child)
		child.site.heap.remove_claim(child)
		self.active_children.remove(child)
		
	def create_child(self, direction):
		claim = Claim(self.gameMap, self.gameMap.getLocation(self.loc, direction), parent = self, dir = util.getOppositeDir(direction), root = self.root)
		self.potential_children.add(claim)
		return claim
		
	def activate_child(self, child):
		logger.debug("Activating %s" % child)
		self.active_children.add(child)
		child.site.heap.add_claim(child)
		
	def spread(self):
		if self.cap:
			if balance.claim_complete_conditions(self.root, 0, 0):
				logger.debug("Claim root %s cap %s is already complete with %s" % (self.root, self.root.cap, self.root.strength ))
				return
			elif balance.claim_complete_conditions(self.root, self.root.get_total_production(), 0):
				logger.debug("Claim root %s cap %s will be complete with %s after a wait" % (self.root, self.root.cap, self.root.strength + self.root.get_total_production() ))
			
		self.potential_children.clear()
		for dir in CARDINALS:
			if dir != self.directionToParent and self.gameMap.getSite(self.loc, dir).owner == self.gameMap.playerTag:
				claim = self.create_child(dir)
				logger.debug("Potential child at %s from %s" % (claim, self.loc))
				
		for child in self.potential_children:
			self.activate_child(child)
		
		logger.debug("Checking for top children of %s out of potential_children %s" % (self, debug_list(self.potential_children)))
		current_children = [child for child in self.potential_children if child.is_top_claim()]
		logger.debug("Finding cap children of %s from set: %s" % (self.loc, debug_list(current_children)))
		
			
		if self.cap and current_children and not balance.claim_complete_conditions(self.root, 0, 0):
			children_strength = 0
			children_production = 0 
			for child in current_children:
				children_strength += child.site.strength
				children_production += child.site.production
			logger.debug("current_children of %s" % debug_list(current_children))
			#only cap claims will ever have to choose which children they want
			if balance.claim_complete_conditions(self.root, children_strength, children_production):
				combos = []
				for i in range(len(current_children)):
					i += 1
	
					combo = [claim for claim in next(itertools.combinations(current_children, i))]
					
					logger.debug("Combination: %s" % combo)
					try:
						heapq.heappush(combos, ClaimCombo(self, combo))
					except ValueError:
						claim_logger.debug("Invalid combination")
						pass
		
				logger.debug("Combinations: %s" % debug_list(combos))
				
				[self.deactivate_child(child) for child in set(self.active_children) if not child in combos[0].claims]
			
			if self.active_children:
				logger.debug("Claim %s is now spread to %s" % (self, debug_list(self.active_children)))
				pass
			else:
				logger.debug("Claim %s has no active children!" % self)
				pass
			

	def get_value(self):
		return self.value
		
	def get_parent(self):
		return self.parent
		
	def get_children(self):
		return self.active_children
		
	def is_root(self):
		return self is self.root
	
	# Should really only be used on the root	
	def get_last_gen(self):
		return self.gens[self.max_gen]
	
	# Should really only be used on the root
	def get_as_moves(self):
		logger.debug("Getting moves from %s with cap %s" % (self, self.cap) )
		if self.cap:
			if balance.claim_complete_conditions(self, 0, 0):
				logger.debug("Last Descendants of %s: %s" % (self, debug_list(self.get_last_gen())))
				moves = []
				for child in self.get_last_gen():
					if child.is_top_claim():
						moves.append(Move(child.loc, child.directionToParent))
				logger.debug("Moves: %s" % debug_list(moves) )
				return moves
			else:
				return []
		else:		
			my_move = []
			if self.is_root() and balance.claim_move_conditions(self):
				my_move.append(Move(self.site.loc, self.directionToParent))
			return [move for child in self.active_children for move in child.get_as_moves()] + my_move
			
	def __hash__(self):
		return self.loc.__hash__() + self.directionToParent * 50 * 50
	
	def __lt__(self, other):
		return other.get_value() < self.get_value()
		
	def __str__(self):
		return "%s->%s" % (self.loc.__str__(),self.directionToParent)
		
	def __eq__(self, other):
		return self.loc is other.loc and self.directionToParent is other.directionToParent and self.root is other.root