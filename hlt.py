import random
import math
import copy

import logging

logger = logging.getLogger("bot")

STILL = 0
NORTH = 1
EAST = 2
SOUTH = 3
WEST = 4

DIRECTIONS = [a for a in range(0, 5)]
CARDINALS = [a for a in range(1, 5)]

ATTACK = 0
STOP_ATTACK = 1

class Location:
	def __init__(self, x=0, y=0):
		self.real_x = x
		self.real_y = y
		self.x = int(round(x))
		self.y = int(round(y))
	
	def getRealCenter(self):
		return (self.real_x,self.real_y)
	
	def __str__(self):
		return str((self.x,self.y))

class Site:
	def __init__(self, owner=0, strength=0, production=0, friends = 0, neutrals = 4, enemies = 0):
		self.owner = owner
		self.strength = strength
		self.production = production
		self.friends = friends
		self.neutrals = neutrals
		self.enemies = enemies
	
	def valOrDot(self, value, dotValue):
		if value == dotValue:
			return "."
		else:
			return str(value)
		
	
	def __str__(self):
		f = self.valOrDot(self.friends, 0)
		n = self.valOrDot(self.neutrals, 4)
		e = self.valOrDot(self.enemies, 0)
		o = self.valOrDot(self.owner, 0)
		return "%s%s%s%s" % (o,f,n,e)
	
		
class Move:
	def __init__(self, loc=0, direction=0):
		self.loc = loc
		self.direction = direction

class Territory:
	def __init__(self, owner):
		self.count = 0
		self.territory = set()
		self.frontier = []
		self.center = None
		
	
	def addLocation(self, location):
		if self.center:
			sum_x = sum([location.x + self.center.real_x * self.count])
			sum_y = sum([location.y + self.center.real_y * self.count])
			
			real_x = sum_x/float(self.count + 1)
			real_y = sum_y/float(self.count + 1)
			
			self.center = Location(real_x, real_y)
		else:
			self.center = location
		self.count += 1
		
		self.territory.add(location)
		
	def getCenter(self):
		return self.center
		
	def getFrontier(self):
		return self.frontier
		
	def findFrontiers(self, map):
		for l in self.territory:
			site = map.getSite(l)
			if site.friends < 4:
				self.frontier.append((site.production, l))
				logger.debug("%s is frontier" % l)
			else:
				logger.debug("%s is not frontier" % l)
		
		
class GameMap:
	def __init__(self, width = 0, height = 0, numberOfPlayers = 0):
		self.width = width
		self.height = height
		self.contents = []
		self.territories = {}

		for y in range(0, self.height):
			row = []
			for x in range(0, self.width):
				row.append(Site(0, 0, 0))
			self.contents.append(row)
	
	def inBounds(self, l):
		return l.x >= 0 and l.x < self.width and l.y >= 0 and l.y < self.height

	def getDistance(self, l1, l2):
		dx = abs(l1.x - l2.x)
		dy = abs(l1.y - l2.y)
		if dx > self.width / 2:
			dx = self.width - dx
		if dy > self.height / 2:
			dy = self.height - dy
		return dx + dy

	def getAngle(self, l1, l2):
	
		dx = l2.x - l1.x
		dy = l2.y - l1.y

		if dx > self.width - dx:
			dx -= self.width
		elif -dx > self.width + dx:
			dx += self.width

		if dy > self.height - dy:
			dy -= self.height
		elif -dy > self.height + dy:
			dy += self.height
		return math.atan2(dy, dx)

	def getLocation(self, loc, direction):
		l = copy.deepcopy(loc)
		if direction != STILL:
			if direction == NORTH:
				if l.y == 0:
					l.y = self.height - 1
				else:
					l.y -= 1
			elif direction == EAST:
				if l.x == self.width - 1:
					l.x = 0
				else:
					l.x += 1
			elif direction == SOUTH:
				if l.y == self.height - 1:
					l.y = 0
				else:
					l.y += 1
			elif direction == WEST:
				if l.x == 0:
					l.x = self.width - 1
				else:
					l.x -= 1
		return l
		
	def getSite(self, l, direction = STILL):
		l = self.getLocation(l, direction)
		return self.contents[l.y][l.x]
	
	def getTerritory(self, owner):
		if not self.territories.get(owner):
			self.territories[owner] = Territory(owner)
		return self.territories[owner]

	def clearTerritories(self):
		self.territories = {}
		
	def __str__(self):
		s = "\n"
		
		# Header row
		for j in range(len(self.contents[0])):
			s = "%s\t%d" % (s,j)
		s = "%s\n" % s
		
		for i in range(len(self.contents)):
			# Header column
			row = self.contents[i]
			s = "%s%d" % (s,i)
			
			for column in row:
				s = s + "\t" + str(column)
			s = s + "\n"
		return s
	
