from hlt import *
import socket
import heapq
import traceback
import struct
from ctypes import *
import sys
import logging

logger = logging.getLogger('bot')

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

	logger.debug("Updating neighbors of %s" % (loc))
	
	if owner == playerTag:
		type = "friends"
	else: 
		type = "enemies"
	
	for dir in CARDINALS:
		newLoc = map.getLocation(loc, dir)
		site = map.getSite(newLoc)
		old = getattr(site, type)
		setattr(site, type, old + 1)
		site.neutrals = site.neutrals - 1
		logger.debug("Updating %s... %s" % (str(newLoc), site) )


def deserializeMap(inputString):
	splitString = inputString.split(" ")

	m = GameMap(_width, _height)

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
				m.getTerritory(owner).addLocation(loc)
			x += 1
			if x == m.width:
				x = 0
				y += 1
		
	for a in range(0, _height):
		for b in range(0, _width):
			m.contents[a][b].strength = int(splitString.pop(0))
			m.contents[a][b].production = _productions[a][b]

			
	#for _,t in m.territories.items():
	#	t.findFrontiers(m)
	
	#m.getTerritory(playerTag).findFrontiers(m)
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
	m = deserializeMap(getString())

	return (playerTag, m)

def sendInit(name):
	sendString(name)

def getFrame():
	return deserializeMap(getString())

def sendFrame(moves):
	sendString(serializeMoveSet(moves))
