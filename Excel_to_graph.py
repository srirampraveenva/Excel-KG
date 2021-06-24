
import numpy 
import pandas as pd
import networkx as nx

def Type(a):
    
    if(a ==  numpy.datetime64):
        return "DATE"
    elif(a == numpy.int64 or a == numpy.float64):
        return "INT"
    elif(a == str):
        return "VARCHAR"
    


def convert_nodes(path):

    df = pd.read_excel(path, sheet_name=None)  
    i = 1
    nodes = list()
    temp = dict()
    for key in df.keys(): 
        temp  = dict()
        temp['labelV'] = key
        for keys in df[key].keys():
            
            temp[keys]= Type(type(df[key][keys].unique()[0]))
        nodes.append((i, temp ))
        i+=1
    G = nx.Graph()
    G.add_nodes_from(nodes)
    return G



G = nx.Graph()    
G=convert_nodes('test.xlsx')
nx.write_graphml(G, "graph_excel.graphml")