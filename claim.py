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
		
def get_claim_strength(claim):
		return claim.site.strength
		
def get_inbound_children(loc):
	inbound = []
	for site in loc.gameMap.neighbors(loc, n=1):
		try:
			if site.heap.get_best_claim().get_parent().site.loc == loc:
				inbound.append(site.heap.get_best_claim())
		except (AttributeError, IndexError):
			continue
	return inbound
		
		
def find_loc_move(loc, depth=0):
	children = get_inbound_children(loc)
	logger.debug("\tFiltering (depth = %s) children of %s: %s" % (depth, loc, debug_list(children)) )	
	moveable_children = [child for child in children if child.will_move()]
	logger.debug("moveable_children of %s: %s" % (loc, debug_list(moveable_children)) )	
	
	self = loc.site.heap.get_best_claim()
	
	fake = False
	if not self:
		fake = True
		self = UncappedClaim(loc.gameMap, loc)
		self.gen = 2

	best = self.get_best_children(moveable_children)
	total_str = 255
	if best:
		total_str = sum([child.site.strength for child in best]) + self.site.strength + self.site.production
	for child in children:
		# if self.is_capped() and self.site.enemies:
			# logger.debug("Avoiding %s because breach" % loc)
			# try:
				# child.site.heap.pop_claim()
				# new_parent_loc = child.site.heap.get_best_claim().get_parents()[0].loc
				# logger.debug("Recursing to new parent")
				# find_loc_move( new_parent_loc, depth+1)
				# logger.debug("Recursing to new child")
				# find_loc_move( child.site.loc, depth+1)
			# except (AttributeError, IndexError):
				# pass
		
		logger.debug("Lazy load these moves, creating the move objects is taking a ton of time")
		if child in best and (self.is_capped() or self.is_checker_on()):
			logger.debug("MOVE child %s accepted by parent %s" % (child.move, loc) )
			child.site.heap.filter_to_loc(loc)
			pass
		elif child.will_move() :
			logger.debug("MOVE child %s rejected by parent %s" % (child.move, loc) )
			child.site.heap.filter_out_loc(loc)
			
			try:
				new_parent_loc = child.site.heap.get_best_claim().get_parent().loc
				logger.debug("Recursing to new parent")
				find_loc_move( new_parent_loc, depth+1)
				logger.debug("Recursing to new child")
				find_loc_move( child.site.loc, depth+1)
			except (AttributeError, IndexError):
				pass
			
	# raise Exception("The uncapped claims aren't pulling the closest ones...")
	if loc.site.owner == loc.gameMap.playerTag:
		total_str = sum([child.site.strength for child in get_inbound_children(loc)]) + self.site.strength
		if self.will_move() and not fake and (self.is_capped() or not self.is_checker_on()):
			loc.site.heap.filter_to_loc(self.get_parent_loc())
			logger.debug("Willing to move %s to %s" % ("HNESW"[self.get_parent_direction()], self.get_parent_loc()) )
			return
		# elif not self.will_move():
			# self.move.setDirections(STILL)
			# raise Exception("The tiles capped claims were moving prematurely so we need something to keep them still in the right circumstances but this isn't quite right yet.")
		elif best and total_str > 255:
			logger.debug("Overflow expected at %s because of %s" % (self, debug_list(best)) )
			biggest = max(best, key=get_claim_strength)
			self.dir = util.getOppositeDir(biggest.get_parent_direction())
			return
		else:
			logger.debug("Choosing to stay STILL, not rechecking old parent yet")
			
			self.dir = STILL

def get_loc_move(loc):
	if loc.site.heap.get_best_claim():
		claim = loc.site.heap.get_best_claim()
		return Move(claim.loc, claim.dir)
	else:
		logger.debug("Rejected by all directions, staying STILL")
		return Move(loc, STILL)

class ClaimHeap:
	def __init__(self, site):
		self.heap = []
		self.site = site
		site.heap = self
		
	def add_claim(self, claim):
		# if claim in self.heap:
			# raise Exception("Something wasn't paying attention")
		old_best = self.get_best_claim()
		#logger.debug("Before adding the claim %s to %s" % (claim, debug_list(self.heap)))
		heapq.heappush(self.heap, (claim))
		# Once a claim in in a heap, you can reference the heap with simply claim.heap
		claim.set_heap(self)
		# #logger.debug("Added the claim %s to %s" % (claim, debug_list(self.heap)))
		self.check_heap(old_best)
		return True
		
	def pop_claim(self):
		best = self.get_best_claim()
		parent = best.get_parent()
		parent.deactivate_child(best)
		return best
	
	def filter_to_loc(self, loc):
		old_best = self.get_best_claim()

		copy = list(self.heap)
		for claim in self.heap:
			# this is a problem for roots?
			if loc is not claim.get_parent().loc:
				copy.remove(claim)
				claim.set_heap(None)
				
		self.heap = copy
		heapq.heapify(self.heap)
		self.check_heap(old_best)
		logger.debug("Removed all children from %s that would come to %s" % (self.site.loc, loc ) )
	
	def filter_out_loc(self, loc):
		old_best = self.get_best_claim()

		copy = list(self.heap)
		for claim in self.heap:
			# this is a problem for roots?
			if loc is claim.get_parent().loc:
				copy.remove(claim)
				claim.set_heap(None)
				
		self.heap = copy
		heapq.heapify(self.heap)
		self.check_heap(old_best)
		logger.debug("Retained only children from %s that would come to %s" % (self.site.loc, loc ) )
	
	def get_next_best(self):
		self.pop_claim()
		return self.get_best_claim()
		
	def remove_claim(self, claim):
		old_best = self.get_best_claim()
		# logger.debug("Removing claim old heap: %s" % debug_list(self.heap))
		
		# This heapify call isn't stable - it changes the best of the heap when I remove one that isn't the best
		# I'm trying to solve this in the __lt__() for claims
		self.heap = [c for c in self.heap if c is not claim]
		# #logger.debug("claim preheapify: %s" % debug_list(self.heap))
		heapq.heapify(self.heap)
		
		claim.set_heap(None)
		# #logger.debug("Removing claim new heap: %s" % debug_list(self.heap))
		# #logger.debug("Removed the claim %s from %s" % (claim, self.site.loc))
		self.check_heap(old_best)
			
		
	def check_heap(self, old_best):
		new_best = self.get_best_claim()
		# if the best changes, then cancel the old best and issue the new best
		if old_best is not new_best:
			# logger.debug("old_best was %s but new_best is %s" % (old_best, new_best))
			# raise Exception("This should probably flag a childless folk as actually needing reinspection")
			if old_best:
				#logger.debug("Unspread the claim on %s from %s" % (old_best, debug_list(old_best.get_parents())))
				# old_best.unspread()
				old_best.root.remove_gen(old_best)
				self.check_root(old_best.root)
				old_best.get_parent().top_children.remove(old_best)
				#logger.debug("Checking completeness of %s" % old_best.root)
			if new_best:
				new_best.root.add_gen(new_best)
				self.check_root(new_best.root)
				new_best.get_parent().top_children.append(new_best)
		
		
	def check_root(self, root):
		# #logger.debug("Checking retrigger of %s" % root)
		if root.is_capped():
			old_expanding_value = root.still_expanding
			if balance.claim_complete_conditions(root):
				root.done_expanding()
			else:
				root.keep_expanding()
			if root.still_expanding and not old_expanding_value:
				logger.debug("Retriggering the childless of %s: %s" % (root, debug_list(root.childless)))
				pass
			else:
				# #logger.debug("Update does not require a retrigger")
				pass
		else:
			# #logger.debug("Uncapped may require a retrigger because a capped claim could spread to far and then get pruned into not needing the location, then the uncapped has no way of getting it back.")
			# #logger.debug("Uncapped update does not require a retrigger")
			pass
				
				
					
		
	def get_best_claim(self):
		if self.heap:
			return self.heap[0]
		return None
		
			
	def __iter__(self):
		return self.heap.__iter__()		
			
	def __str__(self):
		return "%s" % self.site.loc
		
class ClaimCombo:
	def __init__(self, parent, combo):
		self.parent = parent
		self.production = 0
		self.strength = 0
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
		
	def __len__(self):
		return len(self.claims)
		
	def __lt__(self, other):
		return balance.claim_combo__lt__(self, other)
		
	def __str__(self):
		return "V:%s - %s" % (self.value, debug_list(self.claims))
		
	def __getitem__(self, index):
		return self.claims[index]

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
			
	
		for i in range(len(claims)):
			i += 1
			for combo in itertools.combinations(claims, i):
				combo = list(combo)
				try:
					heapq.heappush(combos, ClaimCombo(parent, prefix+combo))
				except ValueError:
					#logger.debug("Invalid combination")
					pass
		for combo in combos:
			#logger.debug("%s" % combo )
			pass
		return combos[0]
	
	def get_parent_loc(self):
		return self.get_parent().loc
	
	def get_total_production(self):
		p = 0
		for i in range(1, self.max_gen+1):
			#logger.debug("Adding %s production to %s because gen %s waiting" % (self.gens[i].production,self.strength, i))
			p += self.gens[i].production
		return p

	def set_heap(self, heap):
		self.heap = heap
		if heap:
			# logger.debug("Setting heap of %s to %s" % (self,heap))
			pass
		else:
			# logger.debug("Clearing heap of %s" % (self))
			pass
		
	def is_top_claim(self):
		# logger.debug("Top %s: %s" % (self,self.heap))
		best = self.site.heap.get_best_claim()
		return best is self
		
	def add_gen(self, child):
		# logger.debug("Adding child %s to gen: %s" % (child,self.gens.get(child.gen, "BLANK")))
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
		#logger.debug("Added %s with str %s, root %s now at %s" % (child,child.strength,self.root, self.strength))
		self.childless.add(child)
		return True
		
	def remove_gen(self, child):
		# logger.debug("Removing child %s from gen: %s" % (child,self.gens.get(child.gen, "BLANK")))
		#logger.debug("Removing %s of gen %s from root %s (max_gen: %s - %s)" % (child,child.gen,self, self.max_gen, debug_list(self.gens[child.gen].claims)))
		self.strength -= child.strength
		#logger.debug("Discarding rather than removing because it may not have been a top child to start. Strength now at %s" % self.strength)
		self.gens[child.gen].discard(child)
		
		if child.gen == self.max_gen and len(self.gens[child.gen]) < 1:
			self.max_gen -= 1
		
		self.strength -= child.production * (self.max_gen - child.gen)
		
		self.childless.discard(child)
		self.childless.add(child.get_parent())
			
	def create_child(self, direction):
		child_loc = self.gameMap.getLocation(self.loc, direction)
				
		if self.is_capped():
			claim = CappedClaim(self.gameMap, location = child_loc, parent = self, dir = util.getOppositeDir(direction), root = self.root)
		else:
			claim = UncappedClaim(self.gameMap, location = child_loc, parent = self, dir = util.getOppositeDir(direction), root = self.root)
		return claim
		
	def done_expanding(self):
		logger.debug("Stopping the expansion of %s cap %s" % (self,self.cap))
		
		self.still_expanding = False
		
	def keep_expanding(self):
		# #logger.debug("Keeping the expansion of %s cap %s" % (self,self.cap))
		self.still_expanding = True
	
	def get_top_children(self):
		return self.top_children
		

	def is_checker_on(self):
		result = ((self.loc.x % 2 == self.loc.y % 2) == (self.gameMap.turnCounter % 2 != 0))
		logger.debug("(%s == %s) == (%s != 0) ? %s" % (self.loc.x % 2, self.loc.y % 2, self.gameMap.turnCounter % 2, result))
		return result
	
	def get_value(self):
		return self.value
		
	def get_parent(self):
		return self.parent
		
	def get_children(self):
		return self.active_children
		
	def is_root(self):
		return self.gen == 0
	
	# Should really only be used on the root	
	def get_last_gen(self):
		return self.gens[self.max_gen]
				
	def get_parent_direction(self):
		return self.dir
	
	# def __hash__(self):
		# if not self.loc:
			# return 0
			
		# #primes = [2,3,5,7,11]
		# #product = 1
		# #max_product = 2310
		# #for dir in self.get_parent_direction():
		# #	product *= primes[dir]
		# max_hash = 2500
		# hash = (self.root.loc.__hash__() * max_hash) + self.loc.__hash__()
		# # #logger.debug("HASH check: %s" % (hash))
		# return hash
	
	def __lt__(self, other):
		#return self.get_value() < other.get_value()
		# if other.value != self.value:
			# return other.value < self.value
		# if other.site.production != self.site.production:
			# return other.site.production < self.site.production
		return other.value < self.value
		
	def __str__(self):
		dirs = self.get_parent_direction()
		dirChars = "HNESW"
		c = dirChars[self.dir]
	 
		capped = self.is_capped() and "C" or "U"
	
		return "%s%s|%s|%.4f|%s->%s%s=>%s" % (capped,self.heap.__str__(),self.site.strength,self.get_value(),c,self.get_parent().loc.__str__(), self.gen,self.root.loc.__str__())
	
	# def __eq__(self, other):
		# # #logger.debug("EQUALITY check: %s vs %s" % (self, other))
		# return self.__hash__() ==  other.__hash__() and self.gen == other.gen and self.is_capped() == other.is_capped()
		# #return self.loc is other.loc and self.get_parents() is other.get_parents() and self.root is other.root and self.gen is other.gen
		
	def is_capped(self):
		return type(self) is CappedClaim
		
	def is_uncapped(self):
		return type(self) is UncappedClaim
	
		
	def get_best_children(self, available_children):
		parent = self
		logger.debug("Parent %s - children %s" % (parent,debug_list(available_children)) )
		#logger.debug("Parent %s - top children %s" % (parent,debug_list(parent.get_top_children())) )

		if not available_children:
			#logger.debug("Parent %s - no available_children" % (parent) )
			return []
		
		#logger.debug("Parent %s - available_children %s" % (parent, debug_list(available_children)) )
		choice_children = set()
		no_choice_children = []
		for child in available_children:
			if any([child.root is c.root for c in child.site.heap if not child is c]):
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
		
		logger.debug("Best combination of %s: %s" % (parent.loc, best) )
		return best

					
					
	
	def spread(self):
		old_max = self.max_gen
		if self.is_uncapped():
			parents = self.gens[self.max_gen]
		elif self.is_capped():
			parents = set(self.childless)
		# raise Exception("This is checking far too many unnecessary childless folks")
		
		if balance.claim_complete_conditions(self, self.get_total_production(), 0):
			logger.debug("%s will be complete next turn" % self)
			self.done_expanding()
			return
		
		save = False
		parent_children = {}
		logger.debug("Expanding parents %s" % (debug_list(parents)))
		for parent in parents:
			if parent.gen != old_max:
				# logger.debug("\tOld parent %s but root at %s" % (parent,self.max_gen))
				pass
			else:
				# logger.debug("\tFresh parent %s at %s" % (parent,self.max_gen))
				pass
			current_children = parent_children.setdefault(parent, set())
			for dir in CARDINALS:
				child_site = self.gameMap.getSite(parent.loc, dir)
				if child_site.owner == self.gameMap.playerTag or (child_site.owner == 0 and child_site.strength == 0):
					# if it's uncapped and checkered, then it only pushes waste_overrides
					# if False and dir in parent.get_parent_direction() and child_site.owner == self.gameMap.playerTag:
					if dir == parent.get_parent_direction():
						# child = parent.create_child(dir)
						# current_children.add(child)
						# parent.activate_child(child)
						# child.waste_override = True
						# # logger.debug("Waste prevention child: %s" % child)
						pass
					else:
						child = parent.create_child(dir)
						current_children.add(child)
						parent.activate_child(child)
						# logger.debug("Normal child: %s" % child)
					
			top_children = parent.get_top_children()		
			for top_child in top_children:
				for child in current_children:
					if child is top_child:
						# logger.debug("Made new top child: %s" % (top_child))
						save = True
				if save:
					break
				
			if len(current_children) == len(top_children):
				if self.is_capped():
					self.childless.remove(parent)
			
		if not save:
			# logger.debug("Couldn't make any top children G:%s for %s" % (self.max_gen, self))
			self.done_expanding()
			return

			
		if balance.claim_complete_conditions(self):
			# logger.debug("Completed the claim with this gen")
			self.done_expanding()
			pass
			
		if self.max_gen == old_max:
			logger.debug("Somehow we didn't increase our gen")
			pass
		

	def unspread(self):
		# #logger.debug("Uncapped so not unspreading")
		return
		
	def activate_child(self, child):
		# logger.debug("Activating %s against %s" % (child, child.site.heap.get_best_claim()) )
		self.active_children.append(child)
		
		child.site.heap.add_claim(child)
		# if child.is_top_claim():
			# # logger.debug("child %s is spread and top" % child)
			# pass
		# else:
			# # logger.debug("child %s is spread but isn't top" % child)
			# pass
		
	def deactivate_child(self, child):
		logger.debug("Deactivation of %s" %(child))
		self.active_children.remove(child)
		child.site.heap.remove_claim(child)
		# logger.debug("Deactivated Result: %s" %(child))
		return
		
	def would_top_claim(self):
		best = self.site.heap.get_best_claim()
		would_top = not best or self.value > best.value
		logger.debug("%s would top %s? %s" % (self,best, would_top))
		return would_top
		
	def will_move(self):
		return balance.claim_move_conditions(self)
		
	def get_best_trail(self):
		depth = min([self.gameMap.getTerritory().production ** .33, 3])
		# logger.debug("Finding trails (p: %s) with depth %s" % (self.gameMap.getTerritory().production, depth))
		# raise Exception("This needs to not be so strong in the early game, and also needs to offer layered pulling in the mid-game")
		
		done = []
		trails = [Trail(claim=self)]
		
		while trails:
			next_trail = trails.pop(0)
			if len(next_trail) >= depth:
				done.append(next_trail)
				continue
			children = next_trail.get_child_trails()
			if children:
				trails.extend(children)
			else:
				done.append(next_trail)
		
		# logger.debug("Trails for %s:" % self)
		heapq.heapify(done)
		best = done[0]
		# logger.debug("Best Trail out of %s: %s" % (len(done), debug_list(best)))
		while done:
			next = heapq.heappop(done)
			# logger.debug("Trail: %s" % (next))
			pass
		return best

	
class Trail:
	def __init__(self, trail=None, new_loc=None, claim=None):
		assert claim is not None or (trail is not None and new_loc is not None)
		if claim:
			self.loc = claim.loc
			self.site = claim.site
			self.claim = claim
			self.gameMap = claim.gameMap
			self.path = [claim.loc]
			self.benefit = balance.evalSiteProduction(self.site)
			self.cost = balance.evalSiteStrength(self.site)
			self.value = self.benefit / self.cost
		elif trail and new_loc:
			self.path = list(trail.path) + [new_loc]
			self.loc = new_loc
			self.site = new_loc.site
			self.gameMap = trail.gameMap
			self.benefit = trail.benefit + balance.evalSiteProduction(self.site)
			self.cost = trail.cost + balance.evalSiteStrength(self.site)
			self.value = self.benefit / self.cost
		else:
			raise Exception("Unable to initialize Trail with %s, %s, %s" % (claim, trail, new_loc))
		
		
	def get_child_trails(self):
		children = []
		for dir in CARDINALS:
			new_loc = self.gameMap.getLocation(self.path[-1], dir)
			if new_loc.site.owner == 0 and not new_loc in self.gameMap.getTerritory().fringe and not new_loc in self.path:
				child = Trail(trail=self, new_loc=new_loc)
				children.append(child)
		return children

	def __lt__(self, other):
		return other.value < self.value
		
	def __len__(self):
		return len(self.path)
		
	def __iter__(self):
		return self.path.__iter__()
		
	def __str__(self):
		return "%s\t%s" % (self.value, debug_list(self.path))
		
		
		
		
		
		
class UncappedClaim(Claim):
	def __init__(self, map, location = None, parent = None, dir=0, root = None, gen = None):
		self.gameMap = map
		self.dir = dir
		self.loc = location
		self.parent = parent or self
		self.root = root or self
		self.heap = None
		self.site = self.loc.site
		self.cap = location.site.strength
		self.cap = self.root.cap
		self.value = 0
		self.gen = 0
		self.max_gen = 0
		self.strength = 0
		self.production = 0
		
		if self.root is self:
			self.gens = {}
			self.benefit = balance.uncapped_claim_benefit(self)
			self.cost = self.root.cap or 1
			self.value = self.benefit / self.cost
			self.childless = set()
			# self.move = Move(self.loc, STILL)
		else:
			self.gen = parent.gen + 1
			# self.move = Move(self.loc, dir)
			self.benefit = parent.benefit
			self.cost = 5 + self.gen
			self.value = self.root.value * .95**self.gen
			self.strength = self.site.strength
			self.production = self.site.production
				
		self.still_expanding = True
		self.active_children = []
		self.top_children = []
		self.moves = None
		# logger.debug("VAL:%s\t%s\t%s\t%s\t%s" % (self.is_capped(),self.benefit, self.cost, self.value, self.gen))
		pass
			

		
	def build_map_dict(self):
		d = {}
		#logger.debug("Mapping %s" % (self.root))
		for i in range(len(self.gens)):
			#logger.debug("Mapping gen %s of %s: %s" % (i,self.root, self.gens[i]))
			for claim in self.gens[i]:
				##logger.debug("%s from %s" % (claim,claim.root))
				d[claim.loc] = "%s" % moveCharLookup(claim.get_parent_direction())
		return d


		
		
		
		
		
		
		
		
class CappedClaim(Claim):
	def __init__(self, map, location = None, parent = None, dir=0, root = None, gen = None):
		self.gameMap = map
		self.dir = dir or STILL
		self.parent = parent or self
		self.root = root or self
		self.loc = location
		self.heap = None
		self.site = self.loc.site
		self.cap = self.site.strength
		self.cap = self.root.cap
		if not self.cap:
			self.cap = .9999
		self.value = 0
		self.gen = 0
		self.max_gen = 0
		self.strength = 0
		self.production = 0
		if self.root is self:
			self.benefit = balance.evalSiteProduction(self.site, claim = self)
			self.cost = balance.evalSiteStrength(self.site)
			self.value = self.get_best_trail().value
			self.childless = set()
			# self.move = Move(self.loc, STILL)
			self.gens = {}
		else:
			self.gen = parent.gen + 1
			# self.move = Move(self.loc, dir)
			self.benefit = self.root.benefit
			self.cost = parent.cost + self.site.production
			if self.root.site.strength == 0:
				self.value = self.root.value / (self.site.strength or 1)
			else:
				self.value = self.root.value * .9 ** self.gen
			self.strength = self.site.strength
			self.production = self.site.production
		
		self.active_children = []
		self.top_children = []
		self.still_expanding = True
		self.moves = None
		self.waste_override = False
		# logger.debug("VAL:%s\t%s\t%s\t%s\t%s" % (self.is_capped(), self.benefit, self.cost, self.value, self.gen))
		pass
		
			
	
		
	def build_map_dict(self):
		d = {}
		#logger.debug("Mapping %s" % (self.root))
		for i in range(len(self.gens)):
			# logger.debug("Mapping gen %s of %s" % (i,self.root))
			for claim in self.gens[i]:
				# #logger.debug("%s from %s" % (claim,claim.root))
				d[claim.loc] = "%s" % moveCharLookup(claim.get_parent_direction())
		return d