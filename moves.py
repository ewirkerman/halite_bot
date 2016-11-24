from util import *
import logging
import copy
from random import shuffle


moves_logger = logging.getLogger("moves")
base_formatter = logging.Formatter("%(asctime)s : %(levelname)s %(message)s")
log_file_name = 'bot.debug'
hdlr = logging.FileHandler(log_file_name)
hdlr.setFormatter(base_formatter)
hdlr.setLevel(logging.DEBUG)
moves_logger.addHandler(hdlr)
moves_logger.setLevel(logging.ERROR)


STILL = 0
CARDINALS = [1,2,3,4]

def setMapChar(move_dict, move):
	char = " X "
	#moves_logger.debug("Move options: %s" % move)
	loc = move.loc
	dirs = set(move.directions)
	if len(dirs) == 1:
		if 1 in dirs:
			char = " ^ "
		elif 2 in dirs:
			char = " > "
		elif 3 in dirs:
			char = " v "
		elif 4 in dirs:
			char = " < "
		elif 0 in dirs:
			char = " O "
	if len(dirs) == 2:
		if 1 in dirs:
			if 2 in dirs:
				char = " 7 "
			elif 3 in dirs:
				char = " | "
			elif 4 in dirs:
				char = " r "
		elif 2 in dirs:
			if 3 in dirs:
				char = " J "
			elif 4 in dirs:
				char = " - "
		elif 3 in dirs:
			char = " L "
	elif len(dirs) == 3:
		if not 1 in dirs:
			char = " U "
		elif not 2 in dirs:
			char = " [ "
		elif not 3 in dirs:
			char = " n "
		elif not 4 in dirs:
			char = " ] "
	elif len(dirs) == 4:
		char = " + "
			
	move_dict[loc] = char

def getMoveMap(map, moves):
	s = "\n"
	t = map.getTerritory(map.playerTag)
	
	move_dict = {}
	for move in moves:
		setMapChar(move_dict, move)
		
		
	#move_dict = {move.loc: move.direction for move in moves}
	
	# Header row
	for j in range(len(map.contents[0])):
		s = "%s\t%d" % (s,j)
	s = "%s\n" % s
	
	for i in range(len(map.contents)):
		# Header column
		row = map.contents[i]
		s = "%s%d" % (s,i)
		
		for j in range(len(row)):
			column = row[j]
			
			#### This sets the display value of the map
			l = map.getLocationXY(j,i)
			site = map.getSite(l)
			if l in t.fringe and site.strength == 0:
				column = "_"
			elif l in move_dict:
				column = move_dict[l]
			elif l in t.territory:
				column = " . "
			
			####
			s = s + "\t" + str(column)
		s = s + "\t%s\n" % map.row_counts[map.playerTag][i]
	# Footer row
	for j in range(len(map.contents[0])):
		s = "%s\t%d" % (s,map.col_counts[map.playerTag][j])
	s = "%s\n" % s
	return s

class Move:
	def __init__(self, loc=0, direction=0):
		self.loc = loc
		self.directions = []
		self.addDirection(direction)
		
	def addDirection(self, direction):
		if type(direction) == list:
			for d in direction:
				if not d in self.directions:
					self.directions.append(d)
		else:
			if not direction in self.directions:
				self.directions.append(direction)
	
	def getDirections(self):
		return self.directions
	
	def __str__(self):
		return "%s->%s" % (self.loc,self.getDirections())
	

class MoveFork:
	def __init__(self, map, initial_moves):
		self.map = map
		self.move_list = []
		self.unused_moves = set(initial_moves)
		self.used_moves = set()
	
	def check_escapes(self, site):
		best_total = site.projected_str
		best_move = Move(site.loc, STILL)
		shuffle(CARDINALS)
		moves_logger.debug("Route: %s(%s)" % (best_move,best_total) )
		for dir in CARDINALS:
			fsite = self.map.getSite(site.loc, dir)
			if fsite.owner == self.map.playerTag:
				total = fsite.projected_str + site.strength
			else:
				total = fsite.projected_str - site.strength
			if total < best_total:
				best_total = total
				best_move = Move(site.loc, dir)
			moves_logger.debug("Route: %s(%s)" % (Move(site.loc, dir),total) )
		moves_logger.debug("Escape: %s(%s)" % (best_move,best_total) )
		return best_move, best_total
	
	def find_escape(self, site, target):
		site_move, site_total = self.check_escapes(site)
		target_move, target_total = self.check_escapes(target)
		
		if target_total < site_total:
			best_move = target_move
			best_total = target_total
		else:
			best_move = site_move
			best_total = site_total
		moves_logger.debug("Best Escape: %s(%s)" % (best_move,best_total) )
		return best_move
	
	def getMoveStrength(self, move):
		return self.map.getDistance(move.loc,self.map.getTerritory(self.map.playerTag).getCenter())
		
	def resolve_moves_iteratively(self, pending):
		approved = []
		continuing = True
		
		queue = copy.copy(pending) #sorted(pending, key=self.getMoveStrength, reverse=True)
		
		while continuing:
			continuing = False
			new_queue = []
			# moves_logger.debug("Resolving %s moves" % len(queue) )
			for move in queue:
				move_approved = False
				
				site = self.map.getSite(move.loc)
				for direction in move.getDirections():
					target = self.map.getSite(move.loc, direction)
					if target.owner != self.map.playerTag or target.projected_str + site.strength <= 275:
						approved.append(move)
						continuing = True
						move_approved = True
						move.directions = [direction]
						#moves_logger.debug("Old pstr: src=%s%s | tar=%s%s" % (move.loc,site.projected_str,target.loc,target.projected_str) )
						site.projected_str -= site.strength
						if target.owner == self.map.playerTag:
							target.projected_str += site.strength
						else:
							target.projected_str -= site.strength
						#moves_logger.debug("New pstr: src=%s%s | tar=%s%s" % (move.loc,site.projected_str,target.loc,target.projected_str) )
						
				if not move_approved:
					new_queue.append(move)
			queue = new_queue
		
		
		moves_logger.debug("Unable to resolve queue: %s" % debug_list(new_queue))
		moves_logger.debug("Skipping escapes right now")
		#for move in queue:
		#	site = self.map.getSite(move.loc)
		#	target = self.map.getSite(move.loc, move.direction)
		#	approved.append(self.find_escape(site, target))
		return approved
		
	def output_all_moves(self):
		from networkingeric import sendString
		self.move_list = self.resolve_moves_iteratively(pending=self.move_list)
		
		returnString = ""
		for move in self.move_list:
			site = self.map.getSite(move.loc)
			target_site = site = self.map.getSite(move.loc, move.getDirections()[0])
			#moves_logger.debug("Sending: %s (str: %s) dir %s to %s (pstr: %s)" % (move.loc, site.strength, move.getDirections(), target_site.loc, target_site.projected_str) )
			returnString += str(move.loc.x) + " " + str(move.loc.y) + " " + str(move.getDirections()[0]) + " "
		sendString(returnString)
	
	def submit_moves(self, moves, weak=False):
		for move in moves:
			self.submit_move(move)
	
	def submit_move(self, move, weak=False):
		loc = move.loc
	
		site = self.map.getSite(loc)
		if site.strength == 0:
			move = Move(loc, 0)
		
		# This will raise an exception if you try to use a move twice because you won't be able to remove it
		
		moves_logger.debug("Submitting move: %s" % move)

		if weak and not loc in self.unused_moves:
			pass
		
		self.unused_moves.remove(loc)
		self.used_moves.add(loc)
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