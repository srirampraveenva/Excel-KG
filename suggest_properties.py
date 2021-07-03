#TODO Should handle errors
from itertools import combinations
from aenum import NoneType
from gremlin_python import statics
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __, properties
from gremlin_python.process.strategies import *
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.structure.graph import Graph
import numpy
import matplotlib as plt
from pandas import ExcelWriter
import os
'''
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



    def convert_nodes(self, excel_path):
        #Path of excel workbook as input converts to node list [(id1,dict(property: type)), (id2,dict(property: type)) ...]
        df = pd.read_excel(excel_path, sheet_name=None)
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
        path = self.npaths(g, node1_label, node2_label, 1)
        return "Connection exceeds 3 nodes" if (len(path[0])>5) else path
        

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
        
        try:
            G = nx.Graph()
            path_obj = pt.shortestpath(g, excel_node1, excel_node2)
            nx.add_path(G,path_obj[0]) #TODO Adds nodes of graph not excel nodes(is this bad?)
            attrs = dict()
            for vertex in path_obj[0]: #Added [0] because it's shortest path and we only have one path
                temp = dict()
                # if (vertex == path_obj[0][0] ):
                #     for i in property_1.keys():
                #        temp[i] = property_1[i]
                
                # elif (vertex == path_obj[0][-1]):
                #     for i in property_2.keys():
                #         temp[i] = property_2[i]
                #if(bool(temp)):#Checks if temp is empty
                for property in g.V(vertex.id).properties().valueMap(True).toList():
                    temp[property[T.key]] = property[T.value]
                attrs[vertex]=temp
            
            nx.set_node_attributes(G, attrs)
            print("Done")
            #nx.write_graphml(G, "/home/rohan/Documents/test_connection.graphml")
            return G
        except:
            return


        

    def suggest_excel(self, g, excel_path, write_path):
        #TODO The graph adds KG nodes not Excel nodes which makes adding standalone nodes a little difficu;t
        #And should we add excel nodes anyway with properties. 
        #What is the final display
        #Input : graph traversal object and path to excel workbook
        #Ouput : dict("Properties": suggested properties, "Connection": graph object representing relations in excel
        # workbook along with new recommended nodes)
        suggestion = dict()

        suggestion["Properties"] = self.suggest_property(g, excel_path)

        e = excel_node()
        nodes = e.convert_nodes(excel_path)
        G = nx.DiGraph()
        H = nx.DiGraph()
        q = Query()
        for (node1, node2) in combinations(nodes, 2):
            node1_label = node1[1]["labelV"]
            node2_label = node2[1]["labelV"]
            if(type(q.findNode(g, node1_label)) is not str or type(q.findNode(g, node2_label)) is  not str ):

                H =  self.suggest_connection(g, node1_label, node2_label)
                
                if (type(H) is not NoneType):

                    G = nx.compose(G,H)
                    #list_of_graphs.append()
        
        labels = [node[1] for node in G.nodes.data("labelV")]
        remove_nodes = list()
        for node in nodes:
            if (node[1]["labelV"] in labels):
                remove_nodes.append(node)
        for i in remove_nodes:
            nodes.remove(i)                

        T = nx.DiGraph()
        T.add_nodes_from(nodes)
        G = nx.compose(T, G)  
        suggestion["Connection"] = G
        nx.write_graphml(G, write_path)
        return suggestion
    
    def suggest_workbooks(self,g, list_of_paths, write_path):
        #Takes in a list of excel workbook paths, combines into one workbook and runs suggest_excel
        writer = ExcelWriter("output.xlsx")

        for filename in list_of_paths:
            print(filename)
            excel_file = pd.ExcelFile(filename)
            (_, f_name) = os.path.split(filename)
            (f_short_name, _) = os.path.splitext(f_name)
            for sheet_name in excel_file.sheet_names:
                df_excel = pd.read_excel(filename, sheet_name=sheet_name)
                df_excel.to_excel(writer, sheet_name, index=False)

        writer.save()
        return self.suggest_excel(g, "output.xlsx", write_path)

            

"""
class Visualize:

    def draw_graph(self, G):
        
        pos = nx.spring_layout(G)
        
        mapping = dict()
        mapping_edges = dict()
        for i in G.nodes.data():
            mapping[i[0]] = i[1]['labelV']
            
        # for i in G.edges.data():
        #     mapping_edges[(i[0], i[1])] = i[2]['labelE']
            
        nx.draw(G, pos, with_labels=True, labels = mapping)
        nx.draw_networkx_edge_labels(G,pos, edge_labels=mapping_edges)    
"""   

g = traversal().withRemote(DriverRemoteConnection('ws://localhost:8182/gremlin','g'))
'''
p = pathtraversal()
#print(g.V(2).properties().valueMap(True).toList())

#print(g.V(1).values('grade_id').next())
a = p.shortestpath(g, "Area", "GradeParalelo")
print(a)  
'''
Excel_path ="/home/rohan/Documents/KG-main-new-20210620T044337Z-001/KG-main-new/KG-main/test.xlsx"

s = suggest()
#print(s.suggest_property(g, "test.xlsx"))

suggestion = s.suggest_excel(g, Excel_path, "test_connection.graphml")
print("\t\t\tProperty\t\tType")
for i in suggestion['Properties'].keys():
    print("Node label : ", i)
    print("------------------------")
    for j in suggestion['Properties'][i]:
        print("\t\t\t"+str(j[0]) +'\t\t'+str(j[1])) 
    print()

G = nx.Graph()
excel = excel_node()
G.add_nodes_from(excel.convert_nodes(Excel_path))

nx.write_graphml(G, "graph_excel.graphml")

Excel_path1 ="/home/rohan/Documents/KG-main-new-20210620T044337Z-001/KG-main-new/KG-main/test(1).xlsx"
Excel_path2 = "/home/rohan/Documents/KG-main-new-20210620T044337Z-001/KG-main-new/KG-main/test_shortest_path.xlsx"


G = s.suggest_workbooks(g, (Excel_path1, Excel_path2), "/home/rohan/Documents/test_workbook.graphml")



    
