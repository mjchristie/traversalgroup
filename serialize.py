"""
Author: Matt Christie, 2015-2016

Serialize some mathematical objects.
"""

import json
import collections as cl
from math import factorial

import graph as g
from functions import Permutation
from cache import memoized

factorial = memoized(factorial)


# All permutation letters, graph nodes, and set elements are assumed
# to be positive integers.


def perm_to_int(perm):
	"""Encode a permutation as an integer."""
	perm = list(perm)
	position = {p: pos for pos, p in enumerate(perm)}
	i = 0
	for j, k in enumerate(xrange(len(perm) - 1, 0, -1)):
		pos = position[k + 1]
		i += factorial(k) * (k - pos)
		perm.remove(k + 1)
		for p in perm[pos:]:
			position[p] -= 1
	return i


def int_to_perm(i, n=1):
	"""Decode an integer as a permutation."""
	while factorial(n) <= i:
		n += 1
	perm = [0 for _ in xrange(n)]
	for k in xrange(n - 1, -1, -1):
		j, num_zeros = 0, 0
		kf = factorial(k)
		# position within the remaining (nonzero) slots
		pos = k - i / kf
		i %= kf
		placed = False
		while not placed:
			if perm[j] != 0:
				j += 1
			elif num_zeros < pos:
				num_zeros += 1
				j += 1
			else:
				# pos == num_zeros; you've found the right slot
				perm[j] = k + 1
				placed = True
	return Permutation(perm)


def graph_to_int(graph):
	"""Encode a graph as an integer."""
	max_node = len(graph.nodes)
	encoded = 0
	k = 1
	for i, edge in enumerate(g.complete_graph_edges(max_node)):
		if edge in graph.edges:
			encoded |= k
		k <<= 1
	return encoded


def int_to_graph(i, n=1):
	"""Decode an integer as a graph."""
	while 1 << g.choose(n, 2) <= i:
		n += 1
	graph = g.Graph()
	graph.add_nodes(xrange(1, n + 1))
	k = 1	
	for edge in g.complete_graph_edges(n):
		if i & k:
			graph.add_edge(*edge)
		k <<= 1
	return graph


def set_to_int(s):
	"""Encode a set as an integer."""
	n = max(s) if s else 0
	i = 0
	for k in xrange(n):
		if k + 1 in s:
			i |= 1 << k
	return i


def int_to_set(i):
	"""Decode an integer as a set."""
	s = set()
	j = 1
	while i != 0:
		if i & 1:
			s.add(j)
		i >>= 1
		j += 1
	return s


def xprimes(step=1000):
	"""A prime number generator."""

	if step % 2:
		raise ValueError("step is not even")

	primes = [2]
	multiples = [4]  # least multiple of prime at index i in primes not yet marked
	lower = 2
	upper = 4
	
	while True:
		
		# non-prime numbers will live here
		nums = set()
		
		for i, p in enumerate(primes):

			# You've marked everything worth marking (for now)
			if p * p > upper:
				break
			# Pick up marking where you left off
			m = multiples[i]
			
			# Do some marking
			while m < upper:  # upper is even, cannot be prime
				nums.add(m)
				m += p
			
			# Left off on this multiple (save for later)
			multiples[i] = m
		
		# Collect primes between lower and upper
		for i in xrange(lower, upper):  # upper is even, cannot be prime
			if i not in nums:
				yield i
				primes.append(i)
				multiples.append(i + i)  # 2 * i (i is a new prime)
		
		# Got all the primes in this interval; move it up
		lower = upper + 1
		upper += min(upper, step)


def seq_to_int(s):
	"""Encode a sequence of nonnegative integers as a positive integer."""
	i = 1
	for p, j in zip(xprimes(), s):
		i *= p ** j
	return i


def int_to_seq(i):
	"""Decode a positive integer as a sequence of nonnegative integers."""
	s = []
	prime = xprimes()
	while i != 1:
		s.append(0)
		p = next(prime)
		while i % p == 0:
			s[-1] += 1
			i /= p
	return s


def encode_objects(objects, encode):
	"""Encode a set of objects as a string of integers."""
	ints = [encode(obj) for obj in objects]
	return json.dumps(sorted(ints))


def decode_objects(string, decode):
	"""Decode a string of integers as a set of objects."""
	ints = json.loads(string)
	return {decode(i) for i in ints}


def encode_group_class(group_class):
	"""The string representation for a group's class."""
	itemized = [[list(key), val] for key, val in group_class.iteritems()]
	itemized.sort()
	return json.dumps(itemized)


def decode_group_class(group_class_repr):
	"""Get a group class from its string representation."""
	loaded = {tuple(key): value for key, value in json.loads(group_class_repr)}
	return cl.Counter(loaded)


# The functions below comprise the original method used for serializing
# permutations by using a permutation's inversion sequence as an intermediate,
# but the method above was chosen since it embeds shorter permutations in
# longer ones. Ex. 2 1 3 and 2 1 will both be encoded as 1, and 1 is decoded
# as 2 1 by default, but can be explicitly made to be any permutation starting
# with 2 1 by passing the desired length n.


def merge(left, right, inversions):
	"""Merge two sorted lists, building up the original list's inversion sequence."""
	merged = []
	il, ir = 0, 0
	lenl, lenr = len(left), len(right)
	while il < lenl or ir < lenr:
		if il < lenl and ir < lenr:
			if left[il] <= right[ir]:
				merged.append(left[il])
				il += 1
			else:
				elt = right[ir]
				merged.append(elt)
				# elt occurs after elements in the left list, but is less
				# than all remaining elements in the left list. Therefore,
				# there are as many inversions of the form (i, elt) as
				# there are remaining elements in the left list.
				for _ in xrange(lenl - il):
					inversions[elt] += 1
				ir += 1				
		elif il < lenl:
			merged.append(left[il])
			il += 1
		else:
			merged.append(right[ir])
			ir += 1
	return merged


def mergesort(lst, inversions):
	"""Sort a list, building up its inversion sequence."""
	# inversions contains inverted list elements, once for each inversion
	if len(lst) == 1:
		return lst
	cut_idx = (len(lst) + 1) / 2
	left = lst[:cut_idx]
	right = lst[cut_idx:]
	left = mergesort(left, inversions)
	right = mergesort(right, inversions)
	return merge(left, right, inversions)


def invert_merge(left, right, inv_seq):
	"""Unsort a sublist according to an inversion sequence."""
	
	# This was written with trial and error following hunches.
	# Why does this work?
	
	merged = []
	inverted = 0
	il, ir = 0, 0
	lenl, lenr = len(left), len(right)
	while il < lenl or ir < lenr:
		if il < lenl and inv_seq[left[il]] == inverted:
			merged.append(left[il])
			inv_seq[left[il]] = 0
			il += 1
		elif il < lenl and ir < lenr:
			if inv_seq[left[il]] - inverted > inv_seq[right[ir]]:
				merged.append(right[ir])
				inverted += 1
				ir += 1
			else:
				merged.append(left[il])
				inv_seq[left[il]] -= inverted
				il += 1
		elif il < lenl:
			merged.append(left[il])
			inv_seq[left[il]] -= inverted
			il += 1
		else:
			merged.append(right[ir])
			ir += 1	
	return merged


def mergeunsort(arr, inv_seq):
	"""Unsort a list according to an inversion sequence."""
	if len(arr) <= 1:
		return list(arr)
	cut_idx = (len(arr) + 1) / 2
	left = arr[:cut_idx]
	right = arr[cut_idx:]
	left = mergeinvert(left, inv_seq)
	right = mergeinvert(right, inv_seq)
	return invert_merge(left, right, inv_seq)


def long_perm_to_inv_seq(perm):
	"""The inversion sequence of a long permutation."""
	inversions = cl.defaultdict(int)
	in_order = mergesort(list(perm), inversions)
	return [inversions[i] for i in xrange(1, len(perm) + 1)]


def short_perm_to_inv_seq(perm):
	"""The inversion sequence of a short permutation."""
	perm = list(perm)
	inv_seq = [0 for _ in xrange(len(perm))]
	for i in xrange(len(perm)):
		for j in xrange(i + 1, len(perm)):
			if perm[i] > perm[j]:
				inv_seq[perm[j] - 1] += 1
	return inv_seq


def inv_seq_to_int(inv_seq):
	"""Encode an inversion sequence as an integer."""
	n = len(inv_seq) - 1
	return sum(factorial(n - i) * inv_seq[i] for i in xrange(len(inv_seq)))


def int_to_inv_seq(i, n):
	"""Decode an integer as an inversion sequence."""
	inv_seq = []
	while n > 1:
		fct = factorial(n - 1)
		inv_seq.append(i / fct)
		i %= fct
		n -= 1
	inv_seq.append(0)
	return inv_seq


def long_inv_seq_to_perm(inv_seq):
	"""Convert a long inversion sequence to its permutation."""
	# O(nlogn), but significant overhead
	inv_seq = {i + 1: inv_seq[i] for i in xrange(len(inv_seq))}
	return Permutation(mergeunsort(range(1, len(inv_seq) + 1), inv_seq))


def short_inv_seq_to_perm(inv_seq):
	"""Convert a short inversion sequence to its permutation."""
	# O(n^2), but not as much bookkeeping
	perm = [0 for _ in xrange(len(inv_seq))]
	for j, inv_count in enumerate(inv_seq):
		i, num_zeros = 0, 0
		placed = False
		while not placed:
			if perm[i] != 0:
				i += 1
			elif num_zeros < inv_count:
				num_zeros += 1
				i += 1
			else:
				perm[i] = j + 1
				placed = True		
	return Permutation(perm)


def alt_perm_to_int(perm, threshold=None):
	"""Encode a permutation as an integer."""
	if threshold == None:
		threshold = len(perm) + 1
	if len(perm) < threshold:
		inv_seq = short_perm_to_inv_seq(perm)
	else:
		inv_seq = long_perm_to_inv_seq(perm)
	return inv_seq_to_int(inv_seq)


def alt_int_to_perm(i, n, threshold=107):
	"""Decode an integer as a permutation."""
	inv_seq = int_to_inv_seq(i, n)
	if len(inv_seq) < threshold:
		return short_inv_seq_to_perm(inv_seq)
	return long_inv_seq_to_perm(inv_seq)





