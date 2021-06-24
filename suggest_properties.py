

from gremlin_python import statics
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.strategies import *
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.structure.graph import Graph
import numpy
'''
import os
os.chdir("/home/rohan/Documents/KG-main-new-20210620T044337Z-001/KG-main-new/KG-main")
'''
import pandas as pd
import networkx as nx
from kgn_pathfinding import Query
#Try using kgn.py
from itertools import combinations
from gremlin_python.process.traversal import T
  



class excel_node():

    def Type(self, a):
        #Return what type each property of a node is
        if(a == numpy.datetime64):
            return "DATE"
        elif(a == numpy.int64 or a == numpy.float64):
            return "INT"
        elif(a == str):
            return "VARCHAR"



    def convert_nodes(self, path):
        #Path of excel sheet as input converts to node list
        df = pd.read_excel(path, sheet_name=None)
        i = 1
        nodes = list()
        temp = dict()
        for key in df.keys():
            temp = dict()
            temp['labelV'] = key
            for keys in df[key].keys():

                temp[keys]= self.Type(type(df[key][keys].unique()[0]))
            nodes.append((i, temp ))
            i+=1
        '''
        G = nx.Graph()
        G.add_nodes_from(nodes)
        return G
        '''
        return nodes


'''
G = nx.Graph()
excel = excel_node()
G=excel.convert_nodes('/home/rohan/Documents/KG-main-new-20210620T044337Z-001/KG-main-new/KG-main/Inventory Management.xlsx')
nx.write_graphml(G, "graph_excel.graphml")
print(G.nodes.data())
'''


class pathtraversal:
    
    '''
    def createNodes(self, g, path):
        #Creates a graph object for a given path
        G = nx.Graph()
        G.add_node(g.V(path[0].id))
    '''



    def countbirdge(self, g, path):
        #Counts the number of bridge nodes, but noticed that bridge nodes always have an out degree of 0
        #So they will not lie on a path, need to check if this is always true

        count = 0
        for j in path:
            if(len(g.V(j.id).properties('labelB').toList())== 0):
                continue
            else:
                count+=1
        return count
            
    def priortizePaths(self, paths):

        #TODO Incomplete function just finds number of bridge nodes and length of paths and creates a list of tuples
        #Need to check criteria for prioritzation

        temp = list()
        for i in paths:
            temp.append(self.countbridge(i), len(i)-2)
        

    def allpaths(self, g, node1_label, node2_label):
        #Returns all paths between two labels
        q = Query()
        if(type(q.findNode(g, node1_label)) is str or type(q.findNode(g, node2_label)) is str ):
            return "One or both nodes don't exist in KG"
        return g.V(q.findNode(g, node1_label).id).repeat(__.out().simplePath()).until(__.hasId(q.findNode(g, node2_label).id)).path().toList()
    
    def npaths(self, g, node1_label, node2_label, numberofpaths):
        #Returns at most n paths between two labels

        q = Query()
        if(type(q.findNode(g, node1_label)) is str or type(q.findNode(g, node2_label)) is str ):
            return "One or both nodes don't exist in KG"
        return g.V(q.findNode(g, node1_label).id).repeat(__.out().simplePath()).until(__.hasId(q.findNode(g, node2_label).id)).path().limit(numberofpaths).toList()
    
    def shortestpath(self, g, node1_label, node2_label):
        #Returns shortest path between two labels
        # 3 outputs
        # Gives filled list with consecutive vertices
        # Gives an empty list if nodes are in excel but path doesn't exist
        # "One or both nodes don't exist" if either node doesn't exist
        q = Query()
        if(type(q.findNode(g, node1_label)) is str or type(q.findNode(g, node2_label)) is str ):
            return "One or both nodes don't exist in KG"
        #return g.V(q.findNode(g, node1_label).id).repeat(__.out().simplePath()).until(__.hasId(q.findNode(g, node1_label).id)).path().limit(1).toList()
        return self.npaths(g, node1_label, node2_label, 1)

class suggest:

    def newProperty(self, value, node):
        #Between kg and excel nodes which properies are unique for each
        #Helper function for suggest_property 
        suggested_property = list()
        for i in value:            
            if i[1] not in node[1]:
                suggested_property.append((i[1], i[2]))
        return suggested_property

    def suggest_property(self, g, excel_path):
        #Path-Path to excel sheet on system
        #Generate excel nodes and suggest properties for each
        e = excel_node()
        q = Query()
        nodes = e.convert_nodes(excel_path)
        print(nodes)
        suggested_property = dict()
        for node in nodes:
            try:
                kg_properties = g.V(q.findNode(g, node[1]['labelV']).id).properties().valueMap(True).toList()
                value = list()
                for property in kg_properties:
                    value.append(list(property.values()))
                suggested_property[node[1]['labelV']]=self.newProperty(value, node)
            except:
                continue
        return suggested_property
    
    def suggest_connection(self, g, excel_node1, excel_node2):

        pt = pathtraversal()
        #res = [(a[1]['labelV'], b[1]['labelV']) for idx, a in enumerate(excel_nodes) for b in excel_nodes[idx + 1:]]
        
        
        #TODO based on reply to the path finding we can use the methods and return a graph object or just table suggestions
        #Probably better to return graph cause then visualization is easier
        try:
            
            G = nx.Graph()
            path = pt.shortestpath(g, excel_node1, excel_node2)
            print(path)

            path_nodes = list()
            for vertex in path[0]:
                #TODO if multiple paths you have to go through each remove path[0]
                temp = dict()
                
                for property in g.V(vertex.id).properties().valueMap(True).toList():
                    
                    temp[property[T.key]] = property[T.value]
                path_nodes.append((vertex.id, temp))
            
                #G.add_nodes_from(list(property[T.id], temp))
            G = nx.Graph()
            G.add_nodes_from(path_nodes)

            path_nodes_list =list()
            path_edges = list()
            for i in path_nodes:
                path_nodes_list.append(i[0])
            for i in range(len(path_nodes_list)-1):
                path_edges.append((path_nodes_list[i], path_nodes_list[i+1]))
            print(path_edges)
            G.add_edges_from(path_edges)

            #nx.write_graphml(G, "testpath.graphml")
            return G


        except:
            return


g = traversal().withRemote(DriverRemoteConnection('ws://localhost:8182/gremlin','g'))
'''
p = pathtraversal()
#print(g.V(2).properties().valueMap(True).toList())

#print(g.V(1).values('grade_id').next())
a = p.shortestpath(g, "Area", "GradeParalelo")
print(a)  
'''


s = suggest()
#print(s.suggest_property(g, "test.xlsx"))

excel = excel_node()
s.suggest_connection(g,'Attendance', 'Teacher')



