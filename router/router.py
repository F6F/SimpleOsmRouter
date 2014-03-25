#!/usr/bin/python 

import re, string, sys 
import xml.sax as sax
from math import radians, cos, sin, asin, sqrt

print "Hello, World!";

filepath = sys.argv[1]

#print "Calculating from:"+ fromNode + " to:"+ toNode

#print sys.argv[1]

class DictHandler(sax.handler.ContentHandler):

    def __init__(self): 
        self.ergebnis = {} 
        self.schluessel = "" 
        self.wert = ""
	self.id = ""
	self.lon = ""
	self.lat =""
        self.aktiv = None
	self.notecount = 0 

    def setDb(self, db):
	self.db = db
	print "DB given to parser"
        
    def startElement(self, name, attrs): 
        #searching for nodes and store all relevant information
	if name == "node":
		self.aktiv = "node"
		self.db.addNode(attrs["id"],node(attrs["id"],attrs["lat"],attrs["lon"]))
	#searching for ways
	if name == "way":
	    print "<----------------- A new Way Starts here ---------------------------------->"
	    self.notecount = self.notecount + 1 
            self.schluessel = ""
	    self.saveMe = False 
            self.highway = ""
	    self.wert = "" 
	    self.lastNode = None
	    self.streetName = ""
	    if self.aktiv != None:
	    	print "something is strange in here"
	    self.aktiv = "way"
  	    self.id = 0
	    self.id = attrs["id"]
	    self.nodes = []
	    #print "Id des wegs: \t" + attrs["id"]
	    #self.aktiv = name 
            #self.lon = eval(attrs["lon"])
	elif (self.aktiv == "way" and name == "nd"):
		#self.nodes[attrs["ref"]] = node(attrs["ref"])
		#print "suchen ob es den node " + attrs["ref"] + " schon gibt"
		#print "Lon aus DB: " + self.db.getNode(attrs["ref"]).lon
		#add connection between nodes if there is a pref node
		nowNode = self.db.getNode(attrs["ref"])
		self.nodes.append(nowNode)
		if self.lastNode:
			#print "found a old node creating connection"
			connection(self.id,self.lastNode,nowNode)
		else:
			print "no old node saved inna here"
		self.lastNode = nowNode	
	elif (self.aktiv == "way" and name == "tag"):
		#print "tag found"
		if attrs["k"] == "highway":
			#mark connections to beeing saved
			self.highway = attrs["v"]
			self.saveMe = True
		if attrs["k"] == "name":
			#print "Name des wegs: \t" + attrs["v"] 
			self.streetName = attrs["v"]
			self.streetName.encode('ascii','ignore')
			#print "Name des wegs: \t" + streetName.encode('utf8')

    def endElement(self, name): 
        if name == "way": 
            #self.ergebnis[self.schluessel] = self.typ(self.wert) 
            self.aktiv = None
	    if self.saveMe:
	    	print "Connections should be saved! "
		#print "<way id=" + self.id + " highway=" + self.highway + " name=" + self.streetName.encode('ascii',"ignore") + " </way>"
		#saving connecitons
		for i in self.nodes:
		  i.saveConnections()
		print "Nodes:"
		print self.nodes
		self.saveMe = False
	    else:
	      for i in self.nodes:
		i.discardChanges()
	    #print "</way>"


class way():
	def __init__(self,id):
		self.id = id
		print "new way with id: " + self.id + " created"
	
class connection():
	def __init__(self,wayId,node1,node2):
		self.node1 = node1
		self.node2 = node2
		self.wayId = wayId
		node1.addConnection(self)
		node2.addConnection(self)
		print " Connection between: " + node1.id + " and " + node2.id + " created"
	def printConnection(self):
		print "Saved Connection between: " + self.node1.id + " and " + self.node2.id + "! "
		#print "<printing connection done>"
	def getOtherNode(self,node):
		if (node == self.node1):
		  return self.node2
		else:
		  return self.node1
	
class node():
	def __init__(self,id,lat,lon):
		self.id = id
		self.connections = []
		self.tempconnections = []
		self.lat = lat
		self.lon = lon
		self.cameFrom = None
		self.distanceToDest = 0.0 #how the crow flys
		self.distanceFromStart = 0.0
		self.explored = False
		self.known = False
		print "new node with id: " + self.id + " created"
		print "lat: " + self.lat + " lon: " + self.lon
	def addConnection(self,connection):
		self.tempconnections.append(connection)
	def saveConnections(self):
		print "saving connection"
		self.connections.extend(self.tempconnections)
		#delete tmp elements
    		self.tempconnections = []
    	def discardChanges(self):
		print "removing connection from nonway"
		self.tempconnections = []
	def numOfConnections(self):
		#print "this node has: " + str(self.connections) + " Connections"
		return len(self.connections)
	def printConnections(self):
		print self.id + " has " + str(len(self.connections)) + " connecitons they are:"
		for i in self.connections:
			print str(i)
			print i.printConnection()
			#print "back again"
	def getScore(self):
		if self.known:
		  return self.distanceFromStart + self.distanceToDest
		else:
		  print "error: !!!NODE NOT KNOW!!!"
		  return 0.0
	def printNextNodes(self):
	      print "listing other nodes: "
	      for i in self.connections:
		otherNode = i.getOtherNode(self)
		print "id: " + otherNode.id + " lat: " + otherNode.lat + " lon: " + otherNode.lon + " distance: " + str(calcDistance(self,otherNode))
	def raiseKnowledge(self,prefNode,destNode):
	    print "going to know more about: " + self.id + " Score: " + str(self.getScore()) + " prfNode was: " + prefNode.id
	    distanceFromPrefNode = calcDistance(prefNode,self)
	    print "\t distanceFromPrefNode: \t" + str(distanceFromPrefNode)
	    self.distanceFromStart = prefNode.distanceFromStart + distanceFromPrefNode
	    print "\t distanceFromStart: \t " + str(self.distanceFromStart)
	    self.distanceToDest = calcDistance(self,destNode)
	    print "\t distanceToDest: \t" + str(self.distanceToDest)
	    self.cameFrom = prefNode
	    self.known = True

class routingDb():
	def __init__(self):
		print "routing DB created"
		self.listOfNodes = {}
		
	def addNode(self,nodeId,node):
		self.listOfNodes[nodeId] = node
		print "storred Node: " + nodeId + " in list"
		
	def size(self):
		return str(len(self.listOfNodes))
		
		
	def getNode(self,nodeId):
		return self.listOfNodes[nodeId]
	      
	def cleanUp(self):
		print "<----------- Cleaning DB ----------------->"
		#self.printStatus()
		#remove all nodes which dont have anny connection to another
		tmpListOfNodes = {}
		for i in self.listOfNodes:
			if self.listOfNodes[i].numOfConnections() > 0:
			   print "keeping node: " + str(i)
			   tmpListOfNodes[i] = self.listOfNodes[i]
		self.listOfNodes = tmpListOfNodes
		print "<----------- Cleanup Done ---------------->"
		self.printStatus()
		
	def printStatus(self):
		print "<------------ Printing Status --------------->"
		print "We have: " + self.size() + " Nodes"
		for i in self.listOfNodes:
			print "Node " + str(i) + " is in da DB it has: " + str(self.listOfNodes[i].numOfConnections()) + " Connection(s)"
			self.listOfNodes[i].printConnections()
	      
		
def readDb(dateiname,db): 
    print dateiname
    handler = DictHandler() 
    handler.setDb(db)
    parser = sax.make_parser() 
    parser.setContentHandler(handler)
    parser.parse(dateiname) 
    print handler.notecount
    return handler.ergebnis
  
def findNextNodes(node):
    node.printConnections()
    node.printNextNodes()
    nextNodes = []
    for i in node.connections:
       nextNodes.append(i.getOtherNode(node))
    print "Next Nodes: "
    print nextNodes
    return nextNodes
    #for i in node.connections:
    #  otherNode = i.getOtherNode(node)
    #  print "id: " + otherNode.id + " lat: " + otherNode.lat + " lon: " + otherNode.lon + " distance: " + str(calcDistance(node,otherNode))

def calcDistance(node,otherNode):
      lat1 = float(node.lat)
      lon1 = float(node.lon)
      lat2 = float(otherNode.lat)
      lon2 = float(otherNode.lon)
      
      #Code coppied form: http://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
      """
      Calculate the great circle distance between two points 
      on the earth (specified in decimal degrees)
      """
      # convert decimal degrees to radians 
      lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

      # haversine formula 
      dlon = lon2 - lon1 
      dlat = lat2 - lat1 
      a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
      c = 2 * asin(sqrt(a)) 

      # 6367 km is the radius of the Earth
      km = 6367 * c
      return km 

def findTopNode(knownNodes):
    topNode = knownNodes[0]
    for i in knownNodes:
      if (topNode.getScore() > i.getScore()):
	print "comparing: \n\t" + str(topNode.id) + " Score: " + str(topNode.getScore()) + " and: \n\t" + i.id + " Score: " + str(i.getScore())
	topNode = i
    print topNode.id + " has the best Score!"
    return topNode
  
def startRouting(db):
    print "<------------ Starting Routing --------------->"
    exploredNodes = []
    knownNodes = []
    tmpNodes = []
    startId = "1554790199"
    endId = "280095678"
    maxSteps = 40
    startNode = db.getNode(startId)
    endNode = db.getNode(endId)
    print "start Ziehl distanz: " + str(calcDistance(startNode,endNode))
    #startNode.printConnections()
    
    nowNode = startNode
    knownNodes.append(nowNode)
    
    while ((nowNode != endNode) & (len(knownNodes) > 0) & (maxSteps > 0)):
      print "<< This is Step: " + str(maxSteps) + " >>"
      #maxSteps = maxSteps - 1    
      knownNodes.remove(nowNode)
      exploredNodes.append(nowNode)
      nowNode.explored = True
      tmpNodes.extend(findNextNodes(nowNode))
      for i in tmpNodes:
	  #	def raiseKnowledge(self,prefNode,destNode):
	  i.known = True
	  if (i.explored == False):
	    i.raiseKnowledge(nowNode,endNode)	
	    if (i in knownNodes):
	      print i.id + " is allread known"
	    else:
	      knownNodes.append(i)
      print "I know some Nodes: "
      for i in knownNodes:
	print i.id
      print "I explored some Nodes: "
      for i in exploredNodes:
	print i.id
      
      nowNode = findTopNode(knownNodes)
    
    print "DONE"
    
    print "I came to " + nowNode.id
    while (nowNode.cameFrom != None):
      print " via " + nowNode.cameFrom.id + "\t Link: http://www.openstreetmap.org/node/"+nowNode.cameFrom.id
      nowNode = nowNode.cameFrom


db = routingDb()
print readDb(open(filepath,"r"),db)
db.cleanUp()
startRouting(db)
