from hlteric import *
import socket
import heapq
import traceback
import struct
from ctypes import *
import sys
import logging
import traceback

bot_logger = logging.getLogger('bot')
map_logger = logging.getLogger('map')
map_logger.setLevel(logging.DEBUG)	

base_formatter = logging.Formatter("%(asctime)s : %(levelname)s %(message)s")
log_file_name = 'bot.debug'
hdlr = logging.FileHandler(log_file_name)
hdlr.setFormatter(base_formatter)
hdlr.setLevel(logging.DEBUG)
map_logger.addHandler(hdlr)

_productions = []
_width = -1
_height = -1
playerTag = -1

def serializeMoveSet(moves):
	returnString = ""
	for move in moves:
		returnString += str(move.loc.x) + " " + str(move.loc.y) + " " + str(move.direction) + " "
	return returnString

def deserializeMapSize(inputString):
	splitString = inputString.split(" ")

	global _width, _height
	_width = int(splitString.pop(0))
	_height = int(splitString.pop(0))

def deserializeProductions(inputString):
	splitString = inputString.split(" ")

	for a in range(0, _height):
		row = []
		for b in range(0, _width):
			row.append(int(splitString.pop(0)))
		_productions.append(row)

def increment_neighbors(map, loc, owner):
	if owner == 0:
		return
	#map_logger.debug("Updating neighbors of %s" % (loc))
	curr_site = map.getSite(loc)
	t = map.getTerritory(owner)
	t.addLocation(loc)
	
	if owner == playerTag:
		type = "friends"
	else: 
		type = "enemies"
	try:
		for dir in CARDINALS:
			#map_logger.debug("loc %s, dir %s" % (loc, dir))
			new_loc = map.getLocation(loc, dir)
			#map_logger.debug("Found %s" % new_loc)
			new_site = map.getSite(new_loc)
			reverse_dir = (((dir - 1) + 2) % 4) + 1
			type_list = getattr(new_site, type).append((loc, dir))
			new_site.neutrals = new_site.neutrals - 1
			
	except:
		traceback.print_exc()

def deserializeMap(m, inputString):
	logger.debug("DeserializING MAP")
	splitString = inputString.split(" ")


	y = 0
	x = 0
	counter = 0
	owner = 0
	while y != m.height:
		counter = int(splitString.pop(0))
		owner = int(splitString.pop(0))
		
		for a in range(0, counter):
			m.contents[y][x].owner = owner
			loc = Location(x,y)
			increment_neighbors(m, loc, owner)
			if owner > 0:
				m.updateCounts(owner, loc)
				m.getTerritory(owner).addLocation(loc)
			x += 1
			if x == m.width:
				x = 0
				y += 1
		
	for a in range(0, _height):
		for b in range(0, _width):
			m.contents[a][b].strength = int(splitString.pop(0))
			m.contents[a][b].production = _productions[a][b]

	
	return m

def sendString(toBeSent):
	toBeSent += '\n'

	sys.stdout.write(toBeSent)
	sys.stdout.flush()

def getString():
	return sys.stdin.readline().rstrip('\n')

def getInit():
	global playerTag
	playerTag = int(getString())
	deserializeMapSize(getString())
	deserializeProductions(getString())
	map_logger.debug("Caching map relations")
	m = GameMap(_width, _height, playerTag = playerTag)
	for y in range(m.height):
		for x in range(m.width):
			l = Location(x,y)
			for dir in DIRECTIONS:
				m.cacheLocation(l, dir)
	deserializeMap(m, getString())
	

	
	return (playerTag, m)

def sendInit(name):
	sendString(name)

def getFrame():
	m = GameMap(_width, _height, playerTag = playerTag)
	deserializeMap(m, getString())
	m.defineTerritories()
	return m

def sendFrame(moves):
	sendString(serializeMoveSet(moves))