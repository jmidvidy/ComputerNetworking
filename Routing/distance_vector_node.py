# -*- coding: utf-8 -*-
"""
EECS 340, Fall 2018
Lab3: Distance Vector Routing

@author: Jeremy Midvidy, jam658
"""

from simulator.node import Node
import json
import copy

# --------------------------------------------- #
# ------------ DV IMPLEMENTATION -------------- #
# --------------------------------------------- #

class Distance_Vector_Node(Node):
    """
    Initalize Routing Table for Node X (with ID_x)
    RT = {
             X: {Dest1 : [cost, latency], Dest2 [cost, latency]}
            N1: {Dest1 : [cost, latency], Dest2 [cost, latency]}
            N2: {Dest1 : [cost, latency], Dest2 [cost, latency]}
            N3: {Dest1 : [cost, latency], Dest2 [cost, latency]}
        }
    
    The Distance Vector of X is RT[x]
    The keys, [X, N1, N2, N3] etc ... are all valid Node.ID's.
    ALL ENTRIES WILL BE STORED AS STRINGS 
    """
    def __init__(self, id):
        super().__init__(id)
        self.myID = str(self.id)
        myID = str(self.id)
        # initalize Routing Table and DV for myID
        self.RT = {}
        self.Neighbors = {}                         # myID, seqNum
        self.RT[myID] = {myID : ['0', myID], "ID" : [myID, '0']}
        print("initalized", myID, "with RT", self.RT)

    def printRT(self):
        for key in self.RT:
            currDV = self.RT[key]
            add = ""
            if key == self.myID:
                add = "(THIS DV)"
            print("\t-------------------------------")
            print("\t\tDV for:", currDV["ID"][0], add)
            for elem in currDV:
                if elem != "ID" and elem != currDV["ID"] and elem != "N":
                    print("\t| Dest:",elem,"| Cost:" , currDV[elem][0], "| Hop:", currDV[elem][1], "|")
        print("\t-------------------------------")
        print("\tNeighbors")
        print("\t", self.Neighbors)
        print("\t-------------------------------")
        return

    # Return a string
    def __str__(self):
        # print ID
        # print Distance Vector
        # maybe add history of updates or something
        
        return ""
    
    """
    Update routing table based on new information.
    """
    def updateRT(self):
        oldDV = copy.deepcopy(self.RT[self.myID])
        oldSeqNum = int(oldDV["ID"][1])
        newSeqNum = str(1 + oldSeqNum)
        destinations = {}
        
        # for every possible destinaiton, find and [cost hop] that links to it
        # {d1: [[c1 h1 fp], [c2 h2 fp], [c3 h3 fp]], d2: [[c1 h1 fp], [c2, h2 fp], [c3, h3 fp]]} 
        for curr in self.Neighbors:
            cost_AT_CURR = int(self.Neighbors[curr])
            if curr in destinations:
                destinations[curr].append([str(cost_AT_CURR), curr, [curr]])
            else:
                destinations[curr] = [[str(cost_AT_CURR), curr, [curr]]]
            
            currDV = self.RT[curr]
            for dest in currDV:
                # ignore ID and self-reference
                if dest == "ID" or dest == currDV["ID"]:
                    continue
                if dest not in destinations:
                    destinations[dest] = []
                
                # currDV = {d1 : [c1 h1], d2: [c2 d2], d3: [c3 d3]} etc...
                cost = cost_AT_CURR + int(currDV[dest][0])
                destinations[dest].append([str(cost), curr, [curr]])
                
        # for every possible destination, find min cost
        newDV = {"ID": [self.myID, newSeqNum], self.myID : ["0", self.myID]}
        for key in destinations:
            currDest = destinations[key]
            # find min cost pair
            min_cost = 1000000000000
            min_cost_pair = []
            for elem in currDest:
                if int(elem[0]) < min_cost:
                    min_cost = int(elem[0])
                    min_cost_pair = elem
            newDV[key] = copy.deepcopy(min_cost_pair)
        
        # update RT and see if need to send message out
        self.RT[self.myID] = newDV
        
        # if keys are not the same --> update
        if set(newDV.keys()) != set(oldDV.keys()):
            self.send_to_neighbors(json.dumps(newDV))
            print("Made Updates!")
            return
            
        # if keys are not the same but values in the keys are not the same --> update
        else:
            for key in newDV:
                if key == "ID":
                    continue
                valOld = oldDV[key]
                valNew = newDV[key]
                if valOld[0] != valNew[0]:
                    self.send_to_neighbors(json.dumps(newDV))
                    print("Made Updates!")
                    return
                if valOld[1] != valNew[1]:
                    self.send_to_neighbors(json.dumps(newDV))
                    print("Made Updates!")
                    return
        return

    """
    When a link is updated: 3 things can happen:
        (1) The current node is given a new neighbor
        (2) The current node is given a link-cost change
        (3) The current node's neighbor is deleted from the Network
        
    (1) The current node is given a new neighbor:
        - Add the new node to the RT with {new: [0, new], "ID": new, myID:[latency, myID]} as an inital value
        - Add the new node to the current node's DV with {new: [latency, new]} as an initial value
        - Send all neighbors the current node's updated DV
        
    (2) The current node is given a link-cost update:
        - Recalculate the current node's optimal path to update node using RT
        - If a change, send all neighbor's the current node's DV
    
    (3) The current node's neighbor is deleted from the Netowrk
        - latency = -1; Delete Neighbor from self.Neighbors
        - UpdateRT
        
    -----------
    """
    def link_has_been_updated(self, neighbor, latency):
        # -1 implies link deletions
        
        neighbor = str(neighbor)
        lat = str(latency)
        
        print("--------------------------------------------------------------------")
        print("\t\t~~UPDAING LINK~~\n")
        print("At", self.myID, "\nOld RT is:")
        self.printRT()
        
        # see if adding new neighbor:
        if neighbor not in self.Neighbors:
            self.RT[neighbor] = {"ID": [neighbor, "0"], neighbor: ["0", neighbor]}
            print("Adding new neighbor!")
            self.Neighbors[neighbor] = lat
            self.updateRT()
            
        
        # update to link-cost (might have to reform for deletions)
        else:
            if latency == -1:
                print("Removing Node!")
                del self.Neighbors[neighbor]
                self.updateRT()
            else:
                print("Updaing link-cost!")
                self.Neighbors[neighbor] = lat
                self.updateRT()
        
        print("New RT:")
        self.printRT()
        return

    """
    When the current node recieves a Distance Vector from a neighbor in the form:
            - Reconstruct this node's DV from infromation in the routing table:
            - change newID in RT to be new DV
            - for all destinations, find shortest path
                - if neighbor, make sure path is shorter than direct-cost
            - if DV has been updated, change
                
    """
    def process_incoming_routing_message(self, m):
        # load to dict
        newDV = json.loads(m)
        newID = newDV["ID"][0]
                            
        print("--------------------------------------------------------------------")
        print("\t\t~~NEW MESSAGE~~")
        print("\tAt Node:", self.myID, "From Node:", newID, "\n")
        oldSeqNum = self.RT[newID]["ID"][1]
        newSeqNum = newDV["ID"][1]
        print("Old Seq Num for Incoming DV at", newID, "is:", oldSeqNum)
        print("New Seq Num for Incoming DV at", newID, "is:", newSeqNum)
        if int(newSeqNum) < int(oldSeqNum):
            print("\tIncoming DV is old!")
            print("\tIgnoring incoming DV!")
            return
        else:
            print("\tUpdaing RT!")
        print("Old RT:")
        self.printRT()
        self.RT[newID] = newDV
        print("Updating RT!")
        self.updateRT()
        print("New RT:")
        self.printRT()
        return

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        print("-------------------------------------------")
        print("IN HOP!")
        print("At Node:", self.myID, "Destination", destination)
        self.printRT()
        dest = str(destination)
        myDV = self.RT[self.myID]
        if dest not in myDV:
            return -1
        else:
            return int(myDV[dest][1])
        
        return


















