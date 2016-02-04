"""
Author: Matt Christie, 2015-2016

A graph data structure.
"""


import math
import random as r
import itertools as it

import numpy as np

from cache import memoized


def substitute_comb(n, k):
	"""Combinatorial function n-choose-k."""
	return math.factorial(n) / (math.factorial(k) * math.factorial(n - k))

try:
	from scipy.misc import comb
except ImportError:
	comb = substitute_comb


class Graph(object):
	"""A graph data structure."""
	def __init__(self, undirected=True):
		self.nodes = {}
		self.edges = {}
		self.neighbors = {}
		self.undirected = undirected
	
	def __len__(self):
		"""The number of nodes in the graph."""
		return len(self.nodes)
	
	def __eq__(self, obj):
		"""Two graphs are equal if they have equal node and edge dictionaries."""
		if self.__class__ != obj.__class__:
			return False
		return self.nodes == obj.nodes and self.edges == obj.edges

	def __hash__(self):
		"""Hash a graph."""
		nodes = tuple(self.nodes.iteritems())
		edges = tuple(self.edges.iteritems())
		return hash(nodes + edges)
	
	def __repr__(self):
		"""Represent a graph as a string."""
		connector = '<->' if self.undirected else '->'
		repr = ', '.join('%r%s%r' % (n1, connector, n2) for n1, n2 in self.edges)
		return '(%s)' % repr
	
	def add_node(self, node, val=True):
		"""Add a node to the graph."""
		if node not in self.nodes:
			self.nodes[node] = val
			self.neighbors[node] = set()
	
	def add_nodes(self, nodes):
		"""Add nodes to the graph."""
		for node in nodes:
			self.add_node(node)
	
	def del_node(self, node):
		"""Delete a node from the graph."""
		if node in self.nodes:
			while len(self.neighbors[node]) > 0:
				self.del_edge(node, self.neighbors[node].pop())
			del self.nodes[node]
			del self.neighbors[node]
	
	def del_nodes(self, nodes):
		"""Delete nodes from the graph."""
		for node in nodes:
			self.del_node(node)			
	
	def edge(self, n1, n2):
		"""An edge from n1 to n2."""
		if self.undirected:
			if n1 > n2:
				return n2, n1
		return n1, n2
	
	def add_edge(self, n1, n2, val=True):
		"""Add an edge to the graph from n1 to n2."""
		self.add_nodes([n1, n2])
		self.edges[self.edge(n1, n2)] = val
		self.neighbors[n1].add(n2)
		if self.undirected:
			self.neighbors[n2].add(n1)
	
	def add_edges(self, edges):
		"""Add edges to the graph."""
		for edge in edges:
			self.add_edge(*edge)
	
	def del_edge(self, n1, n2):
		"""Delete an edge from the graph."""
		if self.undirected:
			self.neighbors[n2].discard(n1)
		self.neighbors[n1].discard(n2)
		del self.edges[self.edge(n1, n2)]
	
	def del_edges(self, edges):
		"""Delete edges from the graph."""
		for edge in edges:
			self.del_edge(*edge)
	
	def load(self, nodes={}, edges={}, node_vals=False, edge_vals=False):
		"""Load nodes and edges into the graph."""
		self.add_nodes(nodes)
		self.add_edges(edges)
		if node_vals == True:
			self.nodes.update(nodes)
		if edge_vals == True:
			edge_items = edges.iteritems()
			self.edges.update({self.edge(*edge): val for edge, val in edge_items})
	
	def clear(self):
		"""Remove all edges and nodes from the graph."""
		self.del_edges(self.edges)
		self.del_nodes(self.nodes)
	
	def adjacent(self, n1, n2):
		"""See if there's an edge between two nodes."""
		return self.edge(n1, n2) in self.edges

	def order_neighbors(self):
		"""Store nodes' neighbors as sorted lists."""
		for node in self.neighbors:
			self.neighbors[node] = sorted(self.neighbors[node])
	
	def hash_neighbors(self):
		"""Store nodes' neighbors as sets."""
		for node in self.neighbors:
			self.neighbors[node] = set(self.neighbors[node])
	
	def bfs(self, start):
		"""Get nodes in breadth-first search from the starting node."""
		queue = (start for _ in xrange(1))
		visited = {start}
		add_neighbors_of = neighbor_adder(self, visited)
		try:
			while True:
				node = queue.next()
				yield node
				queue = it.chain(queue, add_neighbors_of(node))
		except StopIteration:
			pass
	
	def dfs(self, start):
		"""Get nodes in depth-first search from the starting node."""
		stack = (start for _ in xrange(1))
		visited = {start}
		add_neighbors_of = neighbor_adder(self, visited)
		try:
			while True:
				node = stack.next()
				yield node
				stack = it.chain(add_neighbors_of(node), stack)
		except StopIteration:
			pass
	
	def connected_components(self, connect_method=bfs):
		""""Get the connected components of the graph."""
		# This returns something slightly different for directed graphs.
		nodes = list(self.nodes)
		while len(nodes) > 0:
			cur_component = set(connect_method(self, nodes.pop()))
			yield cur_component
			nodes -= cur_component
	
	def to_networkx(self):
		"""Convert the graph to a networkx graph."""
		# Raises ImportError if networkx is not installed
		import networkx as nx
		graph = nx.Graph() if self.undirected else nx.DiGraph()
		graph.add_edges_from(self.edges)
		for node, val in self.nodes.iteritems():
			graph.node[node]['val'] = val
		for edge, val in self.edges.iteritems():
			graph[edge[0]][edge[1]] = val
		return graph


def neighbor_adder(graph, visited):
	"""Get a function that adds unexplored nodes to the fringe in graph traversal."""
	def add_neighbors_of(node):
		for adj in sorted(graph.neighbors[node]):
			if adj not in visited:
				visited.add(adj)
				yield adj
	return add_neighbors_of

@memoized
def choose(n, k):
	"""Combinatorial function n-choose-k."""
	return int(round(comb(n, k)))


# OEIS A001187: Number of connected labeled graphs with n nodes.
# http://oeis.org/A001187
num_connected_graphs = [
	1, 1, 1, 4, 38, 728, 26704, 1866256, 251548592, 66296291072, 34496488594816,
	35641657548953344, 73354596206766622208, 301272202649664088951808,
	2471648811030443735290891264, 40527680937730480234609755344896
]


def complete_graph_edges(n):
	"""The edges of a complete graph on nodes {1, ..., n}."""
	for k in xrange(2, n + 1):
		for i in xrange(1, k):
			yield i, k
			

def erdos_renyi(n, p):
	"""An Erdos-Renyi random graph of the form G(n, p)."""
	graph = Graph()
	graph.add_nodes(xrange(1, n + 1))
	for edge in complete_graph_edges(n):
		if r.random() < p:
			graph.add_edge(*edge)
	return graph


def clique_max(graph):
	"""The maximum size of a clique in the graph."""
	n = len(graph)
	for k in xrange(n, 0, -1):
		for nodes in it.combinations(graph.nodes, k):
			complete = True
			for n1, n2 in it.combinations(nodes, 2):
				if not graph.adjacent(n1, n2):
					complete = False
					break
			if complete:
				return k


def encoding_bound(n):
	"""The least upper bound of the encoding of a graph with n nodes."""
	return 1 << int(round(comb(n, 2)))



