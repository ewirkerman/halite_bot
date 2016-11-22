from util import *
import logging
from random import shuffle

logger = logging.getLogger("bot")

STILL = 0
CARDINALS = [1,2,3,4]



class Move:
	def __init__(self, loc=0, direction=0):
		self.loc = loc
		self.direction = direction
	
	def __str__(self):
		return "%s->%s" % (self.loc,self.direction)
	

class MoveFork:
	def __init__(self, map, initial_moves):
		self.map = map
		self.move_list = []
		self.unused_moves = set(initial_moves)
		self.used_moves = set()
	
	def find_escape(self, site):
		least_total = site.projected_str
		best_move = Move(site.loc, STILL)
		shuffle(CARDINALS)
		for dir in CARDINALS:
			fsite = self.map.getSite(site.loc, dir)
			total = fsite.projected_str + site.strength
			if total < least_total:
				least_total = total
				best_move = Move(site.loc, dir)
		logger.debug("Escape: %s" % best_move)
		return best_move	
	
		
	def resolve_moves(self, pending):
		approved = []
		
		

		for move in pending:
			target_site = self.map.getSite(move.loc, move.direction)
			approved.append(move)
			
			if target_site.owner != self.map.playerTag or target_site.projected_str <= 255:
				pass
			else:
				escape = self.find_escape(target_site)
				approved.append(escape)
				logger.debug("Escape! %s" % move)
		return approved
		
	def getMoveStrength(self, move):
		return self.map.getDistance(move.loc,self.map.getTerritory(self.map.playerTag).getCenter())
		
	def resolve_moves_iteratively(self, pending):
		approved = []
		continuing = True
		
		queue = sorted(pending, key=self.getMoveStrength, reverse=True)
		
		while continuing:
			continuing = False
			new_queue = []
			logger.debug("Resolving %s moves" % len(queue) )
			for move in queue:
				site = self.map.getSite(move.loc)
				target = self.map.getSite(move.loc, move.direction)
				
				if target.owner != self.map.playerTag or target.projected_str + site.strength <= 255:
					approved.append(move)
					continuing = True
					logger.debug("Old pstr: src=%s%s | tar=%s%s" % (move.loc,site.projected_str,target.loc,target.projected_str) )
					site.projected_str -= site.strength
					if target.owner == self.map.playerTag:
						target.projected_str += site.strength
					else:
						target.projected_str -= site.strength
					logger.debug("New pstr: src=%s%s | tar=%s%s" % (move.loc,site.projected_str,target.loc,target.projected_str) )
					
				else:
					new_queue.append(move)
			queue = new_queue
		
		logger.debug("Unable to resolve: %s" % debug_list(new_queue))
		for move in queue:
			site = self.map.getSite(move.loc)
			approved.append(self.find_escape(site))
		return approved
		
	def output_all_moves(self):
		from networkingeric import sendString
		self.move_list = self.resolve_moves_iteratively(pending=self.move_list)
		
		returnString = ""
		for move in self.move_list:
			site = self.map.getSite(move.loc)
			target_site = site = self.map.getSite(move.loc, move.direction)
			logger.debug("Sending: %s (str: %s) dir %s to %s (pstr: %s)" % (move.loc, site.strength, move.direction, target_site.loc, target_site.projected_str) )
			returnString += str(move.loc.x) + " " + str(move.loc.y) + " " + str(move.direction) + " "
		sendString(returnString)
	
	def submit_moves(self, moves, weak=False):
		for move in moves:
			self.submit_move(move)
	
	def submit_move(self, move, weak=False):
		site = self.map.getSite(move.loc)
		if site.strength == 0:
			move.direction = 0
		
		# This will raise an exception if you try to use a move twice because you won't be able to remove it

		if weak and not mov.loc in self.unused_moves:
			pass
		self.unused_moves.remove(move.loc)
		self.used_moves.add(move.loc)
		self.move_list.append(move)
		
	def get_unused_moves(self):
		return self.unused_moves
	
	def get_used_moves(self):
		return self.used_moves
		
	def fork(self, root_fork):
		mf = MoveFork()
		mf.move_list = copy.copy(self.move_list)
		mf.unused_moves = copy.copy(self.unused_moves)
		mf.used_moves = copy.copy(self.used_moves)
		return mf