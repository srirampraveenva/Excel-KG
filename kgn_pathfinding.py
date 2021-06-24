from gremlin_python import statics
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.strategies import *
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.structure.graph import Graph, Vertex
from gremlin_python.process.traversal import T

from nltk.corpus import wordnet
from bs4 import BeautifulSoup as soup
from urllib.request import urlopen as uReq
from urllib.error import HTTPError
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import collections


class Vertex:

    g = None
    def __init__(self,graph):
        self.g = graph
    
    def list_all(self):
        return self.g.nodes

    def properties(self,vid):
        return self.g.nodes[vid]

    def add_vertex(self,label,prop):
        vertex = tuple([label,prop])
        vertex = [vertex]
        self.g.add_nodes_from(vertex)

    def add_multiple_vertex(self,nodes):
        self.g.add_nodes_from(nodes)

    def delete_vertex(self,vid):
        self.g.remove_node(vid)


class Edge:

    g = None

    def __init__(self,graph):
        self.g = graph

    def add_edge(self,id1,id2,prop):
        edge = tuple([id1,id2,prop])
        edge = [edge]
        self.g.add_edges_from(edge)
    
    def add_multiple_edges(self,edges):
        self.g.add_edges_from(edges)

    def delete_edge(self,id1,id2):
        self.g.remove_edge(id1,id2)

class Import:

    def __init__(self):
        self.graph = None

    def import_graphml(self, file_name):
        G1 = nx.read_graphml(file_name)
        G1 = G1.to_undirected()
        self.graph = G1
        return G1

    def create_graph(self, nodes, edges):
        G2 = nx.Graph()
        G2.add_nodes_from(nodes)
        G2.add_edges_from(edges)
        return G2

    def generate_subg(self, node_name, depth=3):

        ego_graph = nx.ego_graph(self.graph, node_name, radius=depth)
        
        # plot graph 
        nx.draw(ego_graph,with_labels=True)
        plt.show()

        return ego_graph


class Algo:
    def __init__(self):
        self.graph = None

    def join_graphs(self, graph1, graph2):

        '''  
            Converting two graph object to single object
            Adding vertex and edges can be done easily
        ''' 
        G = nx.compose(graph1,graph2)
        l = len(G.nodes)+1
        # List of all nodes in a graph
        g1 = [node for node in graph1.nodes(data=True)]
        g2 = [node for node in graph2.nodes(data=True)]
        
        '''
            Iterate over each node and find similarity between the nodes
            If similarity is more than 50% add bridge node to connect both the nodes
        '''
        for s in g1:
            if 'labelV' in s[1]:
                cb = wordnet.synsets(s[1]['labelV'])
            else:
                continue
            if len(cb)==0:
                continue
            cb = cb[0]

            for e in g2:
                if 'labelV' in e[1]:
                    ib = wordnet.synsets(e[1]['labelV'])
                else:
                    continue
                if len(ib)==0:
                    continue
                ib = ib[0]
                if s[1]['labelV'].lower() == e[1]['labelV'].lower():
                    for i in e[1]:
                        if i not in s[1]:
                            s[1][i] = e[1][i]
                    edg = list(G.edges(e[0]))
                    for i in range(len(edg)):
                        #print([s[0],edg[i][1],{'labelE': 'has'}])
                        G.add_edges_from([(s[0],edg[i][1],{'labelE': 'has'})])
                    G.remove_node(e[0])
                    continue
                # Condition if similarity is more than 50% 
                if ib.wup_similarity(cb)>=0.5:

                    # Lowest hypernym will be bridge node
                    bridgess = cb.lowest_common_hypernyms(ib)
                    lemma = bridgess[0].lemmas()

                    # If that node is already there add only new edge, else add vertex and edges

                    if G.has_node(lemma[0].name()):
                        G.add_edge(e[0],lemma[0].name())
                    else:
                        G.add_nodes_from([(str(l),{"labelB":lemma[0].name()}),])
                        G.add_edges_from([(s[0],str(l),{'labelE': 'has'})])
                        G.add_edges_from([(e[0],str(l),{'labelE': 'has'})])
                        l+=1

                    print(s[1]['labelV'],e[1]['labelV'],end="...............")
                    print(ib.wup_similarity(cb), lemma[0].name())

        return G

class Synonym:
    def find_synonyms(self,string):
        synonym_words = []
        synonym_words.append(string)
        try:
            # Remove whitespace before and after word and use underscore between words
            stripped_string = string.strip()
            fixed_string = stripped_string.replace(" ", "_")
            #print(f"{fixed_string}:")

            # Set the url using the amended string
            my_url = f'https://thesaurus.plus/thesaurus/{fixed_string}'
            # Open and read the HTMLz
            uClient = uReq(my_url)
            page_html = uClient.read()
            uClient.close()

            # Parse the html into text
            page_soup = soup(page_html, "html.parser")
            word_boxes = page_soup.find("ul", {"class": "list paper"})
            results = word_boxes.find_all("div", "list_item")

            # Iterate over results and print
            for result in results:
                synonym_words.append(result.text.strip())

        except HTTPError:
            pass

        return synonym_words

    def add_synonyms(self,nodes):
        for node in nodes:
            synonyms = self.find_synonyms(node[1]['labelV'])
            for syn in synonyms:
                node[1]['$'+syn] = 'Synonym'

        return nodes


class Query:
    def findNode(self,g,name):
        nodes1 = set(g.V().has('labelV',name).toList())
        nodes2 = set(g.V().has('labelB',name).toList())
        nodes = nodes1.union(nodes2)
        if len(nodes)==0:
            return "No such node"
        
        final_node = '0'
        for node in nodes:
            node_name = g.V(node).valueMap(True).toList()[0]['labelV'][0]
            if name == node_name:
                final_node = node
        if final_node == '0':
            final_node = list(nodes)[0]
        
        return final_node

    def extractVertex(self,g,graph):
        tem_vertex = graph['@value']['vertices']
        l = []
        for v in tem_vertex:
            for p in g.V(v).properties():
                if p.label=='labelV':
                    l.append(p.value)
                    break
        return tuple(l)

    def extractEdges(self,g,graph):
        tem_edge = graph['@value']['edges']
        edges = []
        for edg in tem_edge:
            tem = str(edg).split('[')[2].replace('-edge-','').replace(']','')
            tem = tem.split('>')
            try:    
                start = g.V(tem[0]).valueMap(True).toList()[0]['labelV'][0]
            except:
                start = g.V(tem[0]).valueMap(True).toList()[0]['labelB'][0]
            try:
                end = g.V(tem[1]).valueMap(True).toList()[0]['labelV'][0]
            except:
                end = g.V(tem[1]).valueMap(True).toList()[0]['labelB'][0]
            edges.append((start,end))
        return tuple(edges)


    def findTrees(self,g,name,depth):
        node = self.findNode(g,name)
        if node == "No such node":
            return
        subGraph = g.V(node).repeat(__.bothE().subgraph('subGraph').V()).times(depth).cap('subGraph').next()
        vertex = self.extractVertex(g,subGraph)
        edges = self.extractEdges(g,subGraph)
        return (vertex,edges)
        

    def findDescendants(self,g,name,depth):
        node = self.findNode(g,name)
        if node == "No such node":
            return

        subGraph = g.V(node).repeat(__.bothE().subgraph('subGraph').V()).times(depth).cap('subGraph').next()

        tem_vertex = subGraph['@value']['vertices']

        nodes = []

        for ver in tem_vertex:
            for p in g.V(ver).properties():
                if p.label=='labelV':
                    nodes.append((p.value,ver))
                    break
        return tuple(nodes)

    def bfs(self,graph,root,g):
        visited, queue = set(), collections.deque([(root,root)])
        removed = set()
        visited.add(root)

        while queue:

            # Dequeue a vertex from queue
            vertex = queue.popleft()
            if vertex[0] in removed or vertex[1] in removed:
                continue
            flag = 0
            for p in g.V(vertex[0]).properties():
                if p.label=='labelV':
                    flag=1
                    break
            if flag:
                print(maping[vertex[0]],end=' ')
                visited.add(vertex[0])
                for neighbour in graph[vertex[0]]:
                    if neighbour not in visited:
                        queue.append((neighbour,vertex[0]))
            else:
                print("...",maping[vertex[0]],maping[vertex[1]])
                visited.add(vertex[0])
                removed.add(vertex[0])
                for neighbour in graph[vertex[0]]:
                    if neighbour not in visited:
                        print(maping[neighbour],neighbour)
                        response = input()
                        if response == 'y' or response=='Y':
                            graph[vertex[1]].append(neighbour)
                            graph[neighbour].remove(vertex[0])
                            graph[neighbour].append(vertex[1])

                            queue.append((neighbour,vertex[1]))
                        else:
                            graph[neighbour].remove(vertex[0])
                        graph.pop(vertex[0])
        return graph

class pathtraversal:
    q = Query()

    def countbirdge(self, path):
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

        if(type(q.findNode(g, node1_label)) is str or type(q.findNode(g, node2_label)) is str ):
            return "One or both nodes don't exist"
        return g.V(q.findNode(g, node1_label).id).repeat(__.out().simplePath()).until(__.hasId(q.findNode(g, node2_label).id)).path().toList()
    
    def npaths(self, g, node1_label, node2_label, numberofpaths):
        #Returns at most n paths between two labels
        if(type(q.findNode(g, node1_label)) is str or type(q.findNode(g, node2_label)) is str ):
            return "One or both nodes don't exist"
        return g.V(q.findNode(g, node1_label).id).repeat(__.out().simplePath()).until(__.hasId(q.findNode(g, node2_label).id)).path().limit(numberofpaths).toList()
    
    def shortestpath(self, g, node1_label, node2_label):
        #Returns shortest path between two labels
        if(type(q.findNode(g, node1_label)) is str or type(q.findNode(g, node2_label)) is str ):
            return "One or both nodes don't exist"
        return g.V(q.findNode(g, node1_label).id).repeat(__.out().simplePath()).until(__.hasId(q.findNode(g, node1_label).id)).path().limit(1).toList()
    
    def pathToGraph(self, g, path_obj, G):
        # Converts path object to graph object
        nx.add_path(G,path_obj)
        attrs = dict()
        for vertex in path_obj:
            temp = dict()
            for property in g.V(vertex.id).properties().valueMap(True).toList():
                temp[property[T.key]] = property[T.value]
            attrs[vertex]=temp
        
        nx.set_node_attributes(G, attrs)

        return G
        
    
if __name__=="__main__":

    ''' 
        Import graphml file
    '''
    #gra = Import()
    # G3 = gra.import_graphml('g3.graphml')
    # G2 = gra.import_graphml('g2.graphml')
    
    # algo = Algo()
    # G = algo.join_graphs(G2,G3)
    # nx.write_graphml(G, "gf.graphml")

    #G = gra.import_graphml('D:/Python/Knowledge Graph/KG-main-priyank_1/apache-tinkerpop-gremlin-server-3.4.10/data/g.graphml')


    ''' Graph traversal '''
    g = traversal().withRemote(DriverRemoteConnection('ws://localhost:8182/gremlin','g'))
    
    

    ''' Get all the nodes '''
    #l = g.with_('evaluationTimeout', 500).V().toList()
    #print(g.V().has('labelV', 'grade').toList())
    
    # name = input("Enter the word: ")
    name = 'grade'
    q = Query()
    # print(q.findNode(g, name).id)
    # subGraph = q.findTrees(g, name, 1)
    # print(subGraph)
    # print("Descendants")
    # print(q.findDescendants(g, name, 2))
    
    ''' Path traversal between two nodes'''
    #Area and GradeParalelo have 2 paths between them
    G = nx.Graph()
    p = pathtraversal()
    for path in p.allpaths(g, "Area", "GradeParalelo"):
        G=p.pathToGraph(g,path,G)
    nx.write_graphml(G, "g_paths.graphml")
    
    

    # graph = {}
    # edge = []
    # tem_edge = subGraph['@value']['edges']
    
    # for edg in tem_edge:
    #     tem = str(edg).split('[')[2].replace('-edge-','').replace(']','')
    #     tem = tem.split('>')
    #     if tem[0] not in maping or tem[1] not in maping:
    #         continue
    #     if tem[0] not in graph:
    #         graph[tem[0]] = []
    #     graph[tem[0]].append(tem[1])

    #     if tem[1] not in graph:
    #         graph[tem[1]] = []
    #     graph[tem[1]].append(tem[0])

    #     edge.append(tuple(tem))
    # # print(graph)

    # print("output")
    # graph = bfs(graph,maping[name],g)
    # for node in graph:
    #     print(maping[node],end=" -> ")
    #     for i in set(graph[node]):
    #         print(maping[i],end = " ")
    #     print()
    # data = dict()
    # for p in g.E(e).properties():
    #     print(p.value)
    # for p in g.V(v).properties():
    #     data[p.label] = p.value
    # print(data)





    ''' Add vertex '''
    # nodes = [(1, {'labelV': 'grade', 'grade_id': 'INT', 'name': 'VARCHAR'}), (2, {'labelV': 'course', 'course_id': 'INT', 'name': 'VARCHAR', 'grade_id': 'INT'}),
    #          (3, {'labelV': 'classroom', 'classroom_id': 'INT', 'grade_id': 'INT', 'section': 'VARCHAR', 'teacher_id': 'INT'}),
    #          (4, {'labelV': 'classroom_student', 'classroom_id': 'INT', 'studen_id': 'INT'}), (5, {'labelV': 'attendance', 'date': 'Date', 'student_id': 'INT', 'status': 'INT'}),
    #          (6, {'exam_type': 'INT', 'name': 'VARCHAR', 'labelV': 'exam_type'}), (7, {'exam_id': 'INT', 'exam_type': 'INT', 'name': 'VARCHAR', 'labelV': 'exam'}), 
    #          (8, {'labelV': 'exam_result', 'exam_id': 'INT', 'student_id': 'INT', 'course_id': 'INT'}), 
    #          (9, {'labelV': 'student', 'student_id': 'INT', 'email': 'VARCHAR', 'name': 'VARCHAR', 'dob': 'Date', 'parent_id': 'INT'}), 
    #          (10, {'labelV': 'parent', 'parent_id': 'INT', 'email': 'VARCHAR', 'password': 'VARCHAR', 'mobile': 'VARCHAR'}), 
    #          (11, {'teacher_id': 'INT', 'name': 'VARCHAR', 'email': 'VARCHAR', 'dob': 'Date', 'labelV': 'teacher'}) ]
    
    # print(nodes)
    # edges = [(1, 2, {'labelE': 'has'}), (1, 3, {'labelE': 'has'}), (3, 4, {'labelE': 'has'}), (3, 11, {'labelE': 'has'}),
    #          (6, 7, {'labelE': 'has'}), (7, 8, {'labelE': 'has'}), (5, 9, {'labelE': 'has'}), (4, 9, {'labelE': 'has'}), 
    #          (2, 8, {'labelE': 'has'}), (9, 8, {'labelE': 'has'}), (9, 10, {'labelE': 'has'})]

    
    # nodes = [(12, {'labelV': 'Area', 'Area_id': 'INT', 'Name': 'VARCHAR', 'Subjects_id': 'INT'}), (13, {'labelV': 'Subject', 'Subject_id': 'INT', 'Abbreviation': 'VARCHAR', 'Area_id': 'INT', 'ScoreRecords_id': 'INT', 'SubjectGrades_id': 'INT'}), 
    #         (14, {'labelV': 'SubjectGrade', 'SubjectGrade_id': 'INT', 'Grade_id': 'INT', 'Subject_id': 'INT'}), (15, {'labelV': 'Level', 'Level_id': 'INT', 'Name': 'VARCHAR', 'Principle': 'VARCHAR', 'Garde_id': 'INT'}), 
    #         (16, {'labelV': 'Grade', 'Garde_id': 'INT', 'Name': 'VARCHAR', 'Level_id': 'INT', 'Observation': 'VARCHAR', 'Grade_paraleloes_id': 'INT', 'Subject_grades_id': 'INT'}), 
    #         (17, {'labelV': 'ScoreRecord', 'ScoreRecord_id': 'INT', 'Subject_id': 'INT', 'Student_id': 'INT', 'FirstTrimester': 'VARCHAR', 'SecondTrimester': 'VARCHAR', 'ThirdTrimester': 'VARCHAR', 'FinalGrade': 'INT', 'Year': 'DATE'}), 
    #         (18, {'labelV': 'Attendance', 'Attendance_id': 'INT', 'Student_id': 'INT', 'Attended': 'VARCHAR', 'Date': 'DATE'}), 
    #         (19, {'labelV': 'Student', 'Student_id': 'INT', 'Garde_paralelo_id': 'INT', 'Rude': 'VARCHAR', 'Attendance_id': 'INT', 'ScoreRecords_id': 'INT', 'Name': 'VARCHAR', 'Father_name': 'VARCHAR', 'Mother_name': 'VARCHAR', 'Sex': 'VARCHAR', 'Date_of_Birth': 'DATE', 'Mobile_phone': 'VARCHAR', 'Address': 'VARCHAR'}), 
    #         (20, {'labelV': 'GradeParalelo', 'Garde_paralelo_id': 'INT', 'Grade_id': 'INT', 'Staff_id': 'INT', 'Name': 'VARCHAR', 'Student_id': 'INT'}), 
    #         (21, {'labelV': 'Staff', 'Staff_id': 'INT', 'Name': 'VARCHAR', 'Date_of_birth': 'DATE', 'Place_of_birth': 'VARCHAR', 'Sex': 'VARCHAR', 'Mobile_phone': 'INT', 'Address': 'VARCHAR', 'Father_name': 'VARCHAR', 'Mother_name': 'VARCHAR', 'Salary': 'VARCHAR', 'StaffType_id': 'INT', 'Garde_paralelos_id': 'INT'}), 
    #         (22, {'labelV': 'User', 'Username': 'VARCHAR', 'Password': 'VARCHAR'}), (23, {'labelV': 'StaffType', 'Name': 'VARCHAR', 'Staff_id': 'INT'})]
    
    # edges = [(13, 12, {'labelE': 'Area_info'}), (14, 13, {'labelE': 'of_Subject'}), (17, 13, {'labelE': 'subject_info'}), 
    #         (16, 14, {'labelE': 'level_info'}), (16, 15, {'labelE': 'has'}), (16, 20, {'labelE': 'has'}), 
    #         (20, 19, {'labelE': 'has'}), (19, 17, {'labelE': 'has'}), (19, 18, {'labelE': 'has'}), 
    #         (20, 21, {'labelE': 'has'}), (21, 23)]


    '''
        Create grahml file from node and edge list
    '''
    # syn = Synonym()
    # nodes = syn.add_synonyms(nodes)
    
    # G = gra.create_graph(nodes,edges)
    # nx.write_graphml(G, "g2.graphml")


    '''
        Add single data
    '''
    # vet.add_vertex('course',data)    
    #vet.delete_vertex('grade')
    # data = {'grade_id':'INT', 'name':'VARCHAR'}
    #vet.add_vertex('grade',data)
    # print(vet.list_all())
    #vet.add_vertex('4',data)
    #ed.add_edge('grade','course','')

    #nx.draw(G,with_labels=True)
    #plt.show()
    #nx.write_graphml(G1, "graph1.graphml")
    #print(vet.properties('142'))
