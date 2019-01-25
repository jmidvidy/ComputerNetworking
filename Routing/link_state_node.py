# -*- coding: utf-8 -*-
"""
EECS 340, Fall 2018
Lab3: Link-State Routing Implementation

@author: Jeremy Midvidy, jam658
"""

from simulator.node import Node
import json
import copy

# --------------------------------------------- #
# ------------ LS IMPLEMENTATION -------------- #
# --------------------------------------------- #

class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        # initalize LSP
        self.myID = str(self.id)
        self.RT = {}
        self.RT[self.myID] = {"ID" : self.myID, "seqNum" : "0"}
        self.LCSP_table = {}
        
    # helper to print a given Topology
    def printTopology(self):   
        #print(self.RT)
        # print the topology stored at self.RT:
        print("\t-------------------------------")
        for node in self.RT:
            add = ""
            if self.myID == node:
                add = "(THIS Node)"
            print("\tNeighbors for Node:", node, add)
            currLS = self.RT[node]
            for key in currLS:
                if key == "ID" or key == "seqNum":
                    continue
                print("\t", node, "-->", key, "| cost:", currLS[key])
            print("\t-------------------------------")
        return
    
    # helper to print a given LCSP_Table
    def printTable(self):
        table = self.LCSP_table
        print("\t-------------------------------")
        for dest in table:
            cost = table[dest][0]
            print("\t| From:", self.myID, "| Dest:", dest, "| Cost:", cost, "|")
            try:
                path = table[dest][1]
                prev = path[0]
                for p in path[1:]:
                    print("\t", prev, "-->", p)
                    prev = p
                print("\t-------------------------------")
            except:
                continue
        return
        
    """
    Whenever there is an update to a node's topology, need to update SP tree to all nodes
        with Dijkstra's
    """
    def updateTable(self):
        #print(self.RT)
        # gather self values
        
        # if a node has no neighbors, it has NO SHORTEST PATHS!!
        if self.neighbors == []:
            self.LCSP_table = {}
            return
        
        myID = self.myID
        RT = self.RT
        
        # detect loops
        def hasLoop(path):
            if len(path) == len(set(path)):
                return True
            else:
                return False
        # find's the min known path in the set
        # of unvisited vertexes
        def findMinUnvisitedKnownVertex():
            min_val = 10000000000000
            min_vertex = None
            for elem in unvisited:
                curr = table[elem]
                if curr[0] != -1:
                    if curr[0] < min_val:
                        min_val = curr[0]
                        min_vertex = elem
            return min_vertex    
        
        # construct unvisited from self.RT
        # construct LCP_table from dest on unvisited destinations
        unvisited = set(RT.keys()) 
        table = {}
        for elem in unvisited:
            # initalzie table to be dest = [-1, None] where -1 is inf, and None is not yet
            # reach in dijstras
            table[elem] = [-1, []]
            
        # equivalent to starting at table
        # and then removing self.myID from unvisited set
        table[myID] = [0, [myID]]
    
        # ------------------- USE Dijstra's to Update LCSP Table -------------------- #
        # initalize currVertex
        while len(unvisited) != 0:
            currVertex = findMinUnvisitedKnownVertex()
            if currVertex == None:
                self.LCSP_table = table
                return
            currLS = RT[currVertex]
            for dest in currLS:
                if dest == "ID" or dest == "seqNum":
                    continue
                if dest not in unvisited:
                    continue
                # collect AS-Path and EXTEND it to include the current vertex
                currPath = copy.deepcopy(table[currVertex][1])
                currPath.append(dest)
                
                # if currPath contains a loop, continue
                if not hasLoop(currPath):
                    continue
                
                # Collect Path-Cost from start through current path to dest node
                prevCost = table[currVertex][0]
                currCost = prevCost + int(currLS[dest])
                # ------ Update Table at Dest ----- #
                # needs update
                if table[dest][0] == -1:
                    table[dest][0] = currCost
                    table[dest][1] = currPath
                # compare to old value
                else:
                    if table[dest][0] > currCost:
                        table[dest][0] = currCost
                        table[dest][1] = currPath
            # the currVertex is now visited
            unvisited.remove(currVertex)
        #update LCSP
        
        # make sure there are no paths with loops
        
        self.LCSP_table = table
        return

    # Return a string
    def __str__(self):
        return ""

    """
    When a link is updated:
        (1) If latency == -1, delete neighbor from LS of THIS (e.g. del self.RT[self.myID][newID])
        (2) Else:
                - either add a new node to self.RT[self.myID]
                - or updating an existing node in self.RT[self.myID]
        (3) SP Table with Dijstra's
        (4) Update seqNum of self.RT[self.myID]
        (5) Send updates to neighbors
    """
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link
        print("--------------------------------------------------------------------")
        print("\t\t~~ UPDAING LINK ~~\n")
        
        self.printTopology()
        
        newID = str(neighbor)
        lat = str(latency)
        
        # if latency == -1 --> delete link and send_to_neighbors
        if latency == -1:
            print(" Deleting link between", self.myID, "and", neighbor, "!")
            del self.RT[self.myID][newID]
            self.neighbors.remove(neighbor)
            try:
                del self.RT[newID][self.myID]
            except:
                pass
        else:
            # if neighbor is not in self.RT --> adding a new neighbor
            if newID not in self.RT:
                print(" Adding neighbor!")
                self.neighbors.append(neighbor)
                print("\t", self.myID, "-->", neighbor, "| cost:", latency)
            else:
                try:
                    print(" Updating link-cost!")
                    print("\t", self.myID, "-->", neighbor, "| old cost:", self.RT[self.myID][newID])
                    print("\t", self.myID, "-->", neighbor, "| new cost:", lat)
                except:
                    print(" Used ADD_NODE! Need to recieve topology from a neighbor")
                    self.neighbors.append(neighbor)
                    out_message = {"sender" : self.myID, "message" : "ADD_NODE_UPDATE", "top" : self.RT}
                    self.send_to_neighbor(neighbor, json.dumps(out_message))
                    print(self.neighbors)
                    print(" hello")

            # update latency (and add node to currLS if needed)
            self.RT[self.myID][newID] = lat
        
        # update sequence number and send to all neighbors
        oldSeqNum = int(self.RT[self.myID]["seqNum"])
        updateSeqNum = str(oldSeqNum + 1)
        self.RT[self.myID]["seqNum"] = updateSeqNum
        out_message = {"sender" : self.myID, "message" : self.RT[self.myID]}
        print(" Topology is now:")
        self.printTopology()
        print(" Updating Least-Cost Shortest-Path Table!")
        self.updateTable()
        print(" Table is now!")
        self.printTable()
        print( "Sending updates to Neighbors!")
        self.send_to_neighbors(json.dumps(out_message))
        return

    """
    When a node recieves a message:
        (1) See whether incomingSeqNum is greater than existing seqNum for existing node
            - if incomingSeqNum is out-of-date, send up-to-date LSP to sender
        (2) If LSP is up-to-date
            - Update self.RT[newID] with the incoming LSP
            - Update LCSP table with Dijstra's
            - Forward message to all neighbors except sender
    """
    def process_incoming_routing_message(self, m):
        
        message = json.loads(m)
        sender = message["sender"]
        newLS = message["message"]
        try:
            newID = newLS["ID"]
        except:
            newID = "Topology Update from ADD_NODE"
        

        print("--------------------------------------------------------------------")
        print("\t\t~~ NEW MESSAGE ~~")
        print("\tAt Node:", self.myID, "Sender:", sender, "About Node:", newID, "\n")
        
        if self.myID == "5" and sender == "3" and newID == "3":
            print("here")
            print("here")

        # WAS BROADCAST NEIGHBORS TOPOLOGY !! IMPORTANT
        if newLS == "ADD_NODE_UPDATE":
            print(" Got add node update!")
            print(" Chaning topology!")
            print(" Old topology:!")
            self.printTopology()
            newTop = message["top"]
            for key in newTop:
                if key != self.myID:
                    self.RT[key] = newTop[key]
            print(" New Topology!")
            print(" New Least-Cost Shortest-Path Table!")
            self.updateTable()
            self.printTable()
            return

        # need to make sure that incoming ID is in RT
        if newID not in self.RT:
            self.RT[newID] = newLS
            oldSeqNum = -1
        else:
            # get oldSeeqNum
            oldSeqNum = int(self.RT[newID]["seqNum"])
            
        # get incomingSeqNum
        incomingSeqNum = int(newLS["seqNum"])
        
        print(" Making sure SeqNum is up-to-date!")
        print("  Old SeqNum for Incoming LS at node", newID, "is:", oldSeqNum)
        print("  New SeqNum for Incoming LS at node", newID, "is:", incomingSeqNum)
        
        
        # ---------------------- RECIEVES OUT-OF-DATE LS PACKET ---------------------- #
        # if the incoming sequence number is less than
        # old sequence number, send the updated sequence
        # number back from the sender of the packet
        if incomingSeqNum <= oldSeqNum:
            if incomingSeqNum == oldSeqNum:
                print(" Incoming seqNum is the same as previously recieved!")
                print(" Not sending any messages!")
                
                return
            print(" Incoming LS packet from", sender, "is out of date!")
            print(" Sending up-to-date LS packet to", sender)
            out_message = {"sender" : self.myID, "message" : self.RT[newID]}
            self.send_to_neighbor(int(sender), json.dumps(out_message))
            return
        
        # ---------------------- NEEDS TO UPDATE PATHS BASED ON NEW PACKET ---------------------- #
        print(" Original Topology at:", self.myID)
        self.printTopology()
        print(" Updating Node Topology!")
        # update topology at this sequence number
        self.RT[newID] = newLS
        print(" New Topology at:", self.myID)
        self.printTopology()
        print(" Updating Least-Cost Shortest-Path Table!")
        self.updateTable()
        print(" Table is now!")
        self.printTable()
        print(" Sending Updates to Neigbors!")
        # send updates to all neighbors that are not the sender
        print(self.neighbors)
        out_message = {"sender" : self.myID, "message" : newLS}
        for n in self.neighbors:
            
            if n != int(sender):
                self.send_to_neighbor(n, json.dumps(out_message))
                print(" Sent message to:", n)
        return

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        self.updateTable()
        print("-------------------------------------------")
        print("\t\t~~ IN HOP ~~")
        print("At Node:", self.myID, "Destination", destination)
        dest = str(destination)
        print(" Curr Topology!")
        self.printTopology()
        print(" Curr Table!")
        self.printTable()
        if dest not in self.LCSP_table:
            return -1
        else:
            full_path = self.LCSP_table[dest][1]
            hop = full_path[1]
            return int(hop)
    
