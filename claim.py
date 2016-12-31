from hlt2 import *
from networking2 import *
from moves import *
import logging
import heapq
import util
import itertools

def getStrFromMoveLoc(move):
	return move.loc.site.strength
	
def create_claim(gameMap, loc):
	if any([site.enemies for site in gameMap.neighbors(loc, 1, True)]):
		return UncappedClaim(gameMap, loc)
	else:
		return CappedClaim(gameMap, loc)
	

class ClaimHeap:
	def __init__(self, site):
		self.heap = []
		self.site = site
		site.heap = self
		
	def add_claim(self, claim):
		logger.debug("Is %s in %s? %s" % (claim, debug_list(self.heap), claim in self.heap))
		# raise Exception("I shouldn't have any bad merging right now, but I do.  Need to solve this.")
		for c in list(self.heap):
			if c.root is claim.root:
				if c.gen == claim.gen:
					c.merge(claim)
					return True
				elif not claim.is_capped() and c.gen < claim.gen:
					return False
		if not claim in self.heap:
			old_best = self.get_best_claim()
			#logger.debug("Before adding the claim %s to %s" % (claim, debug_list(self.heap)))
			heapq.heappush(self.heap, (claim))
			# Once a claim in in a heap, you can reference the heap with simply claim.heap
			claim.set_heap(self)
			# #logger.debug("Added the claim %s to %s" % (claim, debug_list(self.heap)))
			self.check_heap(old_best)
		return True
		
	def remove_claim(self, claim):
		old_best = self.get_best_claim()
		# #logger.debug("Removing claim old heap: %s" % debug_list(self.heap))
		
		# This heapify call isn't stable - it changes the best of the heap when I remove one that isn't the best
		# I'm trying to solve this in the __lt__() for claims
		self.heap = [c for c in self.heap if c is not claim]
		# #logger.debug("claim preheapify: %s" % debug_list(self.heap))
		heapq.heapify(self.heap)
		
		claim.set_heap(None)
		# #logger.debug("Removing claim new heap: %s" % debug_list(self.heap))
		# #logger.debug("Removed the claim %s from %s" % (claim, self.site.loc))
		self.check_heap(old_best)
		
	def check_root(self, root):
		# #logger.debug("Checking retrigger of %s" % root)
		if root.is_capped():
			if balance.claim_complete_conditions(root):
				root.done_expanding()
			else:
				root.keep_expanding()
			if root.still_expanding:
				#logger.debug("Retriggering the last gen of %s" % root)
				pass
			else:
				# #logger.debug("Update does not require a retrigger")
				pass
		else:
			# #logger.debug("Uncapped may require a retrigger because a capped claim could spread to far and then get pruned into not needing the location, then the uncapped has no way of getting it back.")
			# #logger.debug("Uncapped update does not require a retrigger")
			pass
				
			
		
	def check_heap(self, old_best):
		new_best = self.get_best_claim()
		#logger.debug("old_best was %s" % (old_best))
		#logger.debug("new_best is %s" % (new_best))
		# if the best changes, then cancel the old best and issue the new best
		if old_best is not new_best:
			if old_best:
				#logger.debug("Unspread the claim on %s from %s" % (old_best, debug_list(old_best.get_parents())))
				old_best.unspread()
				old_best.root.remove_gen(old_best)
				self.check_root(old_best.root)
				##logger.debug("Checking completeness of %s" % old_best.root)
			if new_best:
				new_best.root.add_gen(new_best)
				self.check_root(new_best.root)
				
					
		
	def get_best_claim(self):
		if self.heap:
			return self.heap[0]
		return None
		
			
	def __iter__(self):
		return self.heap.__iter__()		
			
	def __str__(self):
		return "%s" % self.site.loc
		
class ClaimCombo:
	def __init__(self, parent, combo, gen_str=0):
		self.parent = parent
		self.production = 0
		self.strength = 0
		self.gen_str = gen_str
		self.claims = combo
		for c in combo:
			self.strength += c.strength
			self.production += c.production
		##logger.debug("Combination: %s" % debug_list(combo))
		if not balance.claim_combo_valid(self):
			raise ValueError("Invalid combination of locations")
		self.value = balance.evaluate_claim_combo(self)
		self.cap = parent.cap
		
	def __iter__(self):
		return self.claims.__iter__()
		
	def __lt__(self, other):
		return balance.claim_combo__lt__(self, other)
		
	def __str__(self):
		return "V:%s - %s" % (self.value, debug_list(self.claims))

class Gen:
	def __init__(self, claims = []):
		self.claims = set(claims)
		self.production = 0
		self.strength = 0
		
	def __iter__(self):
		return self.claims.__iter__()
		
	def __len__(self):
		return self.claims.__len__()
		
	def __str__(self):
		return debug_list(self.claims)
	
	def add(self, child):
		self.claims.add(child)
		self.production += child.production
		self.strength += child.strength
	
	def remove(self, child):
		self.claims.remove(child)
		self.production -= child.production
		self.strength -= child.strength
		
	def discard(self, child):
		self.claims.discard(child)
		self.production -= child.production
		self.strength -= child.strength
		
class Claim:
	def get_best_combination(self, parent, claims, seed=None, prefix=None):
		combos = []
		if seed:
			combos = seed
		if not prefix:
			prefix = []
			
		gen = self.root.gens[self.gen]
		gen_str = gen.strength
		
		for i in range(len(claims)):
			i += 1
			for combo in itertools.combinations(claims, i):
				combo = list(combo)
				try:
					heapq.heappush(combos, ClaimCombo(parent, prefix+combo, gen_str))
				except ValueError:
					#logger.debug("Invalid combination")
					pass
		for combo in combos:
			#logger.debug("%s" % combo )
			pass
		return combos[0]
	
	def get_total_production(self):
		p = 0
		for i in range(self.max_gen+1):
			##logger.debug("Adding %s production to %s because gen %s waiting" % (self.gens[i].production,self.strength, i))
			p += self.gens[i].production
		return p

	def set_heap(self, heap):
		self.heap = heap
		if heap:
			logger.debug("Setting heap of %s to %s" % (self,heap))
			pass
		else:
			logger.debug("Clearing heap of %s" % (self))
			pass
		
	def is_top_claim(self):
		logger.debug("Top %s: %s" % (self,self.heap))
		best = self.heap.get_best_claim()
		return best is self
		
	def add_gen(self, child):
		# #logger.debug("Adding child %s to gen: %s" % (child,self.gens.get(child.gen, "BLANK")))
		self.gens.setdefault(child.gen, Gen())
		# #logger.debug("Adding %s of gen %s to root %s (max_gen: %s - %s)" % (child,child.gen,self, self.max_gen, debug_list(self.gens[child.gen].claims)))
		while child.gen > self.max_gen:
			for i in range(self.max_gen+1):
				# #logger.debug("Adding %s production to %s because gen %s waiting" % (self.gens[i].production,self.strength, i))
				self.strength += self.gens[i].production
			self.max_gen += 1
			# #logger.debug("Max gen now %s" % (self.max_gen))
		self.strength += child.strength
		self.gens[child.gen].add(child)
		##logger.debug("Added %s with str %s, root %s now at %s" % (child,child.strength,self.root, self.strength))
		return True
			
	def remove_parent(self, parent):
		self.parentDirections.pop(parent)
		
	def create_child(self, direction):
		child_loc = self.gameMap.getLocation(self.loc, direction)
				
		if self.is_capped():
			claim = CappedClaim(self.gameMap, location = child_loc, parent = self, dir = util.getOppositeDir(direction), root = self.root)
		else:
			claim = UncappedClaim(self.gameMap, location = child_loc, parent = self, dir = util.getOppositeDir(direction), root = self.root)
		return claim
		
	def done_expanding(self):
		# #logger.debug("Stopping the expansion of %s cap %s" % (self,self.cap))
		
		self.still_expanding = False
		
	def keep_expanding(self):
		# #logger.debug("Keeping the expansion of %s cap %s" % (self,self.cap))
		self.still_expanding = True
		
	def get_top_children(self):
		return [c for c in self.active_children if c.is_top_claim()]
		
	def merge(self, other):
		#logger.debug("Merging two claims: %s and %s" % (self, other))
	
		self.parentDirections.update(other.parentDirections)
		for parent in other.get_parents():
			parent.active_children.remove(other)
			parent.active_children.add(self)
		other.set_heap(self.heap)
		#logger.debug("Merged: %s and %s" % (self, other))

	def get_value(self):
		return self.value
		
	def get_parents(self):
		return list(self.parentDirections.keys())
		
	def get_children(self):
		return self.active_children
		
	def is_root(self):
		return self is self.root
	
	# Should really only be used on the root	
	def get_last_gen(self):
		return self.gens[self.max_gen]
				
	def get_parent_direction(self):
		return list(self.parentDirections.values())
	
	def __hash__(self):
		if not self.loc:
			return 0
			
		#primes = [2,3,5,7,11]
		#product = 1
		#max_product = 2310
		#for dir in self.get_parent_direction():
		#	product *= primes[dir]
		max_hash = 2500
		hash = (self.root.loc.__hash__() * max_hash) + self.loc.__hash__()
		# #logger.debug("HASH check: %s" % (hash))
		return hash
	
	def __lt__(self, other):
		#return self.get_value() < other.get_value()
		if other.get_value() != self.get_value():
			return other.get_value() < self.get_value()
		return other.get_parent_direction() < self.get_parent_direction()
		
	def __str__(self):
		dirs = self.get_parent_direction()
		dirChars = "HNESW"
		c = ""
		for d in dirs:
			c += dirChars[d]
	 
		capped = self.is_capped() and "C" or "U"
	
		return "%s%s|%s|%.4f|%s->%s%s=>%s" % (capped,self.heap.__str__(),self.site.strength,self.get_value(),c,[parent.loc.__str__() for parent in self.get_parents()], self.gen,self.root.loc.__str__())
	
	def __eq__(self, other):
		# #logger.debug("EQUALITY check: %s vs %s" % (self, other))
		return self.__hash__() ==  other.__hash__() and self.gen == other.gen and self.is_capped() == other.is_capped()
		#return self.loc is other.loc and self.get_parents() is other.get_parents() and self.root is other.root and self.gen is other.gen
		
	def is_capped(self):
		return type(self) is CappedClaim
		
	def snip(self):
		parent = self
		#logger.debug("Parent %s - children %s" % (parent,debug_list(parent.get_children())) )
		#logger.debug("Parent %s - top children %s" % (parent,debug_list(parent.get_top_children())) )
		available_children = [child for child in parent.get_top_children() if child.is_capped() or balance.claim_move_conditions(child)]

		if not available_children:
			#logger.debug("Parent %s - no available_children" % (parent) )
			return
		
		#logger.debug("Parent %s - available_children %s" % (parent, debug_list(available_children)) )
		choice_children = set()
		no_choice_children = []
		for child in available_children:
			if any([child.root is c.root for c in child.site.heap if not child is c]) or len(child.parentDirections) > 1:
				choice_children.add(child)
			else:	
				no_choice_children.append(child)					
		#logger.debug("choice_children: %s" % debug_list(choice_children) )
		#logger.debug("no_choice_children: %s" % debug_list(no_choice_children) )
		combos = [ClaimCombo(parent, [])]
		prefix = []
		best = combos[0]
		if no_choice_children:
			best = self.get_best_combination(parent, no_choice_children, seed = combos)
			prefix = best.claims
			combos = [best]
		if choice_children:
			best = self.get_best_combination(parent, choice_children, seed = combos, prefix = prefix)
		
		
		#logger.debug("Best combination of %s: v:%s %s" % (parent.loc, best.value, best) )
		for child in best:
			for other_parent in list(child.get_parents()):
				if other_parent != parent:
					logger.debug("Found a parent %s that isn't %s" % (other_parent, parent) )
					other_parent.deactivate_child(child)
		for child in available_children:
			if child not in best:
				parent.deactivate_child(child)
		logger.debug("Best combination of %s: %s" % (parent.loc, best) )
		
	def would_top_claim(self):
		best = self.site.heap.get_best_claim()
		return self.value > best.value
		
	def will_move(self):
		return balance.claim_move_conditions(self)
		

	
class Trail:
	def __init__(self, claim):
		self.loc = claim.loc
		self.site = claim.site
		self.gameMap = claim.gameMap
		
		self.depth = 2
		
		best_path = None
		
		outer = [[self.loc]]
		for i in range(self.depth):
			next_outer = []
			for path in outer:
				for dir in CARDINALS:
					new_loc = self.gameMap.getLocation(self.loc, dir)
					if new_loc.site.owner == 0 and not new_loc in self.gameMap.getTerritory().fringe and not new_loc in path:
						new_path = list(path)
						new_path.append(self.gameMap.getLocation(self.loc, dir))
						next_outer.append(new_path)
			outer = next_outer
			next_outer = []
	
		logger.debug("Trails for %s:" % claim)
		for path in outer:
			logger.debug("Trail:" % debug_list(path))
	
		
		
		
		
		
		
		
		
		
class UncappedClaim(Claim):
	def __init__(self, map, location = None, parent = None, dir=0, root = None, gen = None):
		if not location and not gen:
			raise ValueError("No seed to work from")
		self.gameMap = map
		self.parentDirections = {}
		if parent:
			self.parentDirections[parent] = dir
		self.heap = None
		self.root = root or self
		
		if location:
			self.loc = location
			self.site = self.loc.site
			self.cap = location.site.strength
			self.cap = self.root.cap
		else:
			#logger.debug("Seed uncapped gen %s"  % debug_list(gen) )
			for real_root in gen:
				real_root.root = self
			self.loc = None
			self.cap = 0
			
		self.value = 0
		self.gen = 0
		self.max_gen = 0
		self.gens = {}
		if self.parentDirections:
			someParent = next(iter(self.parentDirections.keys()))
			self.gen = someParent.gen + 1
		self.strength = 0
		self.production = 0
		
		if self.root is self:
			##logger.debug("Creating a seed claim at %s"  % self.loc)
			self.benefit = balance.uncapped_claim_benefit(self)
			self.cost = self.root.cap or 1
			self.value = self.benefit / self.cost
			self.gens[0] = gen or Gen([self])
			self.gens[0].production = 0
			self.gens[0].strength = 0
		else:
			self.benefit = parent.benefit
			self.cost = 5 + self.gen
			# if self.site.owner != map.playerTag:
				# self.cost += self.site.strength
			self.value = self.root.value * .8**self.gen
			self.strength = self.site.strength
			self.production = self.site.production
				
		self.still_expanding = True
		self.active_children = set()
		self.moves = None
		logger.debug("VAL:%s\t%s\t%s\t%s\t%s" % (self.is_capped(),self.benefit, self.cost, self.value, self.gen))
		pass

	def trigger(self):
		if self.is_top_claim():
			while self.still_expanding:
				# #logger.debug("Spreading the last gen (%s) of %s" % (self.max_gen,self))
				self.spread()

	def spread(self):
		old_max = self.max_gen
		parents = set(self.gens[self.max_gen])
		
		
		for parent in parents:
			for dir in CARDINALS:
				if dir in self.get_parent_direction():
					continue
				child_site = self.gameMap.getSite(parent.loc, dir)
				
				# this is the types of types the claim will spread through
				if child_site.owner == self.gameMap.playerTag or (child_site.owner == 0 and child_site.strength == 0):
					claim = parent.create_child(dir)
					#logger.debug("Potential child at %s" % (claim))
					parent.activate_child(claim)
		
		# we activate them all so that we know which ones are on top of the claim
		
		# if you the max_gen has increased, then we are still expanding
		if old_max == self.max_gen:
			# #logger.debug("Max gen (%s) didn't increase (%s), it must not be able to expand anymore" % (old_max, self.max_gen))
			self.done_expanding()
			
	
	def prune(self):
		parents = set(self.gens[max([self.max_gen - 1, 0])])
		for parent in sorted(parents):
			parent.snip()
			
			
	def unspread(self):
		# #logger.debug("Uncapped so not unspreading")
		return
		
	def activate_child(self, child):
		#logger.debug("Activating %s to the active set %s of %s" % (child, debug_list(self.active_children), self) )
		self.active_children.add(child)
		
		result = child.site.heap.add_claim(child)
		if not result:
			self.active_children.remove(child)
		#logger.debug("Activated %s" % child)
		
	def deactivate_child(self, child):
		# #logger.debug("Deactivation of %s from the parent %s" %(child, self))
		self.active_children.remove(child)
		child.remove_parent(self)
		# if not child.get_parents():
			# child.site.heap.remove_claim(child)
		logger.debug("Deactivated Result: %s" %(child))
		return
		
	def get_as_moves(self):
		#logger.debug("get_as_moves from max_gen %s %s" % (self.max_gen, self) )
		if self.moves is None:
			self.moves = []
			logger.debug("Getting moves from max_gen %s of %s" % (self.max_gen, self) )
			base = 1
			if self.site.enemies and self.site.strength:
				logger.debug("Bumping base up to one for breach")
				base += 1
			for i in range(base,self.max_gen):
				logger.debug("Checking gen %s of %s" % (i, self) )
				for claim in self.gens[i]:
					#logger.debug("Checking child %s" % (claim) )
					logger.debug("Checking claim %s" % (claim) )
					if balance.claim_move_conditions(claim) and claim.site.strength:
						move = Move(claim.loc,claim.get_parent_direction())
						claim.parentDirections = {}
						#logger.debug("Added move: %s" % move )
						self.moves.append(move)
					elif balance.claim_move_conditions_parentless(claim):
						logger.debug("Stuck parentless")
						for dir in CARDINALS:
							location = claim.gameMap.getLocation(claim.loc, dir)
							move = Move(claim.loc, dir)
							logger.debug("Checking move: %s " % location.site.heap.get_best_claim())
							if location in claim.gameMap.getTerritory().fringe and location.site.strength and location.site.heap.get_best_claim().max_gen == 0:
								logger.debug("Moving %s to fringe %s" % (claim, move.loc))
								self.moves.append(move)
								break
		return self.moves
		
	def build_map_dict(self):
		d = {}
		#logger.debug("Mapping %s" % (self.root))
		for i in range(len(self.gens)):
			#logger.debug("Mapping gen %s of %s: %s" % (i,self.root, self.gens[i]))
			for claim in self.gens[i]:
				##logger.debug("%s from %s" % (claim,claim.root))
				d[claim.loc] = "%s" % moveCharLookup(claim.get_parent_direction())
		return d
		
	def remove_gen(self, child):
		#logger.debug("Removing child %s from uncapped gen: %s" % (child,self.gens.get(child.gen, "BLANK")))
		self.strength -= child.strength
		self.gens[child.gen].discard(child)
		#logger.debug("Removing %s of gen %s from root %s (max_gen: %s - %s)" % (child,child.gen,self, self.max_gen, debug_list(self.gens[child.gen].claims)))
		
		
		
		
		
		
		
		
		
		
		
class CappedClaim(Claim):
	def __init__(self, map, location = None, parent = None, dir=0, root = None, gen = None):
		self.gameMap = map
		self.parentDirections = {}
		if parent:
			 self.parentDirections[parent] = dir
		self.heap = None
	
		self.root = root or self
		self.loc = location
		self.site = self.loc.site
		self.cap = self.site.strength
		self.cap = self.root.cap
		if not self.cap:
			self.cap = .9999
		self.value = 0
		self.gen = 0
		self.max_gen = 0
		self.gens = {}
		if self.parentDirections:
			someParent = next(iter(self.parentDirections.keys()))
			self.gen = someParent.gen + 1
		self.strength = 0
		self.production = 0
		if self.root is self:
			self.benefit = balance.evalSiteProduction(self.site, claim = self)
			self.cost = balance.evalSiteStrength(self.site)
			self.value = self.benefit / self.cost
			self.gens[0] = gen or Gen([self])
			self.gens[0].production = 0
			self.gens[0].strength = 0
		else:
				
			self.benefit = self.root.benefit
			self.cost = parent.cost + self.site.production
			self.value = self.benefit / self.cost
			self.strength = self.site.strength
			self.production = self.site.production
		
		self.potential_children = set()
		self.active_children = set()
		self.still_expanding = True
		self.moves = None
		logger.debug("VAL:%s\t%s\t%s\t%s\t%s" % (self.is_capped(), self.benefit, self.cost, self.value, self.gen))
		pass
		
	def trigger(self):
		if self.is_top_claim():
			while (not balance.claim_complete_conditions(self)) and self.still_expanding:
				# #logger.debug("Spreading the last gen (%s) of %s" % (self.max_gen,self))
				self.spread()
				self.prune()
		else:
			self.done_expanding()

	def spread(self):
		old_max = self.max_gen
		parents = set(self.gens[self.max_gen])
		if balance.claim_complete_conditions(self, self.get_total_production(), 0):
			self.done_expanding()
			return
		
		for parent in parents:
			for dir in CARDINALS:
				child_site = self.gameMap.getSite(parent.loc, dir)
				if not dir in parent.get_parent_direction() and child_site.owner == self.gameMap.playerTag:
					claim = parent.create_child(dir)
					parent.activate_child(claim)
					#logger.debug("Parent %s created %s" % (parent,claim) )
		
		# we activate them all so that we know which ones are on top of the claim
		
		
		# if you the max_gen has increased, then we are still expanding
		if old_max == self.max_gen:
			self.done_expanding()
			return
			
	def prune(self):
		if not self.max_gen:
			return
		parents = set(self.gens[self.max_gen-1])
		current_children = self.gens[self.max_gen]
		# #logger.debug("Made a new gen out of %s" % debug_list(current_children))
		children_strength = 0
		children_production = 0 
		for child in current_children:
			children_strength += child.site.strength
			children_production += child.site.production
		##logger.debug("current_children of %s: %s" % (self.root, debug_list(current_children)) )
		
		
		# this call includes the strength of the new generation we just applied
		if not balance.claim_complete_conditions(self.root):
			# self.keep_expanding()
			return
			
		for parent in sorted(parents):
			parent.snip()
					
			
	def unspread(self):
		#rescind all children
		for child in set(self.active_children):
			# #logger.debug("Unspreading %s spread by %s" % (child,self))
			child.unspread()
			##logger.debug("Fully unspread %s" % (child))
			##logger.debug("Now deactivating %s" % (child))
			self.deactivate_child(child)
		
		# #logger.debug("Unspread complete")
		
	def activate_child(self, child):
		# #logger.debug("Activating %s to the active set %s of %s" % (child, debug_list(self.active_children), self) )
		self.active_children.add(child)
		
		child.site.heap.add_claim(child)
		##logger.debug("Activated %s" % child)
	
	def deactivate_child(self, child):
		# #logger.debug("Deaktivating %s, from parent %s and root %s" % (child, self, self.root) )
		# #logger.debug("Current heap: %s" % debug_list(child.site.heap) )
		if self in child.get_parents():
			# #logger.debug("Removing %s from the active set %s of %s" % (child, debug_list(self.active_children), self) )
			self.active_children.remove(child)
			child.remove_parent(self)
			if not child.get_parents():
				child.site.heap.remove_claim(child)
		
		
		logger.debug("Deactivated Result: %s" %(child))
		
	# Should really only be used on the root
	def get_as_moves(self):
		if self.moves is None:
			self.moves = []
			#logger.debug("Getting moves from %s" % self)
			if balance.claim_complete_conditions(self):
				#logger.debug("Last Descendants of %s: %s" % (self, debug_list(self.get_last_gen())))
				for child in self.get_last_gen():
					if child.is_top_claim():
						move = Move(child.loc, child.get_parent_direction())
						#logger.debug("Added move: %s" % (move))
						self.moves.append(move)
				#logger.debug("Moves: %s" % debug_list(self.moves) )
		return self.moves

			
	def remove_gen(self, child):
		#logger.debug("Removing child %s from gen: %s" % (child,self.gens.get(child.gen, "BLANK")))
		#logger.debug("Removing %s of gen %s from root %s (max_gen: %s - %s)" % (child,child.gen,self, self.max_gen, debug_list(self.gens[child.gen].claims)))
		self.strength -= child.strength
		#logger.debug("Discarding rather than removing because it may not have been a top child to start. Strength now at %s" % self.strength)
		self.gens[child.gen].discard(child)
		if not self.gens[child.gen]:
			#logger.debug("Dropping max_gen because a capped claim has an empty gen")
			while child.gen < self.max_gen:
				for i in range(self.max_gen+1):
					self.strength -= self.gens[i].production
				self.max_gen -= 1
				#logger.debug("Max gen now %s" % (self.max_gen))
		else:
			#logger.debug("Not dropping max_gen because a capped claim still has something in the gen")
			pass
		
	def build_map_dict(self):
		d = {}
		##logger.debug("Mapping %s" % (self.root))
		for i in range(len(self.gens)):
			##logger.debug("Mapping gen %s of %s" % (i,self.root))
			for claim in self.gens[i]:
				# #logger.debug("%s from %s" % (claim,claim.root))
				d[claim.loc] = "%s" % moveCharLookup(claim.get_parent_direction())
		return d