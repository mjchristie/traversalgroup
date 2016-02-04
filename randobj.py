"""
Author: Matt Christie, 2015-2016

Generate random objects for the graph_experiments package.
"""

import math
import random as r
import itertools as it

import graph as g


# Not so happy having a "random stuff" module, conceptually.
# Maybe these things would be better distributed among other modules?
# This will do, for now.


def pick(elements, distribution):
	"""Pick an element from an iterable according to a distribution."""
	choice = r.random()
	p = 0.0
	for elt, d in zip(elements, distribution):
		p += d
		if choice < p:
			return elt
	# In the event of numerical error
	return elt


def mask(i):
	"""Stream i as a sequence of 1's and 0's. Least bits come first."""
	while i != 0:
		yield i & 1
		i >>= 1


def random_subsequence(elements, encoding=False):
	"""Choose a random subsequence from the sequence of elements."""
	encoded = r.randint(0, (1 << len(elements)) - 1)
	subsequence = [elt for elt, chosen in zip(elements, mask(encoded)) if chosen]
	if encoding:
		return subsequence, encoded
	return subsequence


def random_spanning_tree(nodes):
	"""A random tree that spans some nodes."""
	# Inspired from Wesley Baugh's answer on
	# http://stackoverflow.com/questions/2041517/random-simple-connected-graph-generation-with-given-sparseness
	visited = set()
	graph = g.Graph()
	graph.add_nodes(nodes)
	cur_node = r.choice(nodes)
	visited.add(cur_node)
	while len(visited) < len(nodes):
		new_node = r.choice(nodes)
		if new_node not in visited:
			graph.add_edge(cur_node, new_node)
			visited.add(new_node)
		cur_node = new_node
	return graph


def random_connected_graph(nodes):
	"""A random connected graph."""
	# Inspired from Wesley Baugh's answer on
	# http://stackoverflow.com/questions/2041517/random-simple-connected-graph-generation-with-given-sparseness
	graph = random_spanning_tree(nodes)
	not_included = []
	make_edge = lambda edge: graph.edge(*edge)
	for edge in it.imap(make_edge, it.combinations(nodes, 2)):
		if edge not in graph.edges:
			not_included.append(edge)
	graph.add_edges(random_subsequence(not_included))
	return graph



