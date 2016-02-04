"""
Author: Matt Christie, 2015-2016

Classes for different types of functions. Currently provides
Bijections and Permutations, with special associated features
for Permutations.
"""

import itertools as it
import collections as cl

from cache import lru_cache


class Bijection(object):
	"""A one-to-one correspondence between two sets of things."""
	def __init__(self, f, inv=None):
		if type(f) != dict:
			raise ValueError("f is not a dictionary")	
		if inv == None:
			# This is a new bijection; copy mapping
			self.f = {key: val for key, val in f.iteritems() if key != val}
			self.finv = {val: key for key, val in self.f.iteritems()}
			self.inv = Bijection(self.finv, inv=self)
		else:
			# This is the inverse of some other bijection; point to argument
			self.f = f
			self.finv = inv.f
			self.inv = inv		

	@property
	def domain(self):
		"""The set of things this bijection maps."""
		return set(self.f)
	
	@property
	def range(self):
		"""The set of things this bijection maps to."""
		return set(self.finv)
	
	def well_defined(self):
		"""Ensure the bijection isn't broken."""
		return self.domain == self.inv.range		
	
	def of(self, bij):
		"""Compose a bijection with another."""
		return {elt: self(bij(elt)) for elt in bij}

	def iteritems(self):
		return self.f.iteritems()
	
	def itervalues(self):
		return self.f.itervalues()

	def __getitem__(self, elt):
		if elt in self.f:
			return self.f[elt]
		return elt
	
	def __call__(self, elt):
		return self[elt]
	
	def __len__(self):		
		return len(self.f)
	
	def __iter__(self):
		return (elt for elt in self.f)
	
	def __contains__(self, elt):
		return elt in self.f

	def __eq__(self, obj):
		if obj.__class__ != self.__class__:
			return False
		longer, shorter = self, obj
		if len(obj) > len(self):
			longer, shorter = obj, self
		return all(longer[elt] == shorter[elt] for elt in longer if longer[elt] != elt)
	
	def __neq__(self, obj):
		return not (self == obj)
	
	def __hash__(self):
		return hash(tuple(sorted((k, v) for k, v in self.f.iteritems() if k != v)))
	
	def __repr__(self):
		repr = ', '.join("%r->%r" % (i, self[i]) for i in self)
		return "(%s)" % repr


class Permutation(Bijection):
	"""A rearrangement of an ordered collection of things."""
	def __init__(self, f, order=None):
		if type(f) is dict:
			self.letters = sorted(f)
			Bijection.__init__(self, f)
		elif type(f) is Bijection:
			self.letters = sorted(f.f)
			Bijection.__init__(self, f.f)
		elif type(f) is Permutation:
			self.letters = f.letters
			Bijection.__init__(self, f.f)
		elif order == None:
			# Assume a simple permutation of the set {1, ..., n}
			self.letters = range(1, len(f) + 1)
			g = dict(it.izip(self.letters, f))
			Bijection.__init__(self, g)
		else:
			# Construct a permutation that maps order to f,
			# retaining the symbols that correspond to the
			# underlying elements {1, ..., n} in self.letters.
			h = {}
			positions = cl.defaultdict(set)
			self.letters = {}
			for i, elt in enumerate(f):
				positions[elt].add(i + 1)
				self.letters[i + 1] = elt
			self.letters = cl.OrderedDict(sorted(self.letters.iteritems()))
			positions = {k: list(reversed(sorted(v))) for k, v in positions.iteritems()}
			for i, elt in enumerate(order):
				h[i + 1] = positions[elt].pop()
			Bijection.__init__(self, h)				
	
	def __iter__(self):
		return (self[elt] for elt in self.letters)

	def __repr__(self):
		repr = ', '.join("%r->%r" % (i, self[i]) for i in self.letters)
		return "(%s)" % repr
	
	def well_defined(self):
		"""Ensure the permutation isn't broken."""	
		return self.domain == self.range
	
	@property
	def cycle_decomposition(self):
		"""The cycle decomposition of the permutation."""
		return CycleDecomposition(self)
	
	@property
	def degree(self):
		"""The degree of the permutation."""
		return len(self)


def cycle_decomposition(perm):
	"""The cycle decomposition of a permutation."""
	cycles = []
	visited = set()
	for lt in perm.letters:
		if perm[lt] not in visited:
			cur_cycle = [perm[lt]]
			visited.add(perm[lt])
			cur_elt = perm[lt]
			while perm[cur_elt] != cur_cycle[0]:
				cur_cycle.append(perm[cur_elt])
				visited.add(perm[cur_elt])
				cur_elt = perm[cur_elt]
			cycles.append(cur_cycle)
	return cycles


class CycleDecomposition(object):
	"""The cycle decomposition of a permutation."""
	def __init__(self, perm):
		self.cycles = cycle_decomposition(perm)
		self.perm = perm
		self.count = CycleCount(self)

	@staticmethod
	def equivalent(p1, p2):
		"""Determine if two permutations' cycle decompositions are equivalent."""
		return p1.cycle_decomposition.count == p2.cycle_decomposition.count
	
	def __repr__(self):
		pieces = ''
		for cycle in self.cycles:
			if len(cycle) > 1:
				letters = ' '.join(repr(lt) for lt in cycle)
				pieces += '(%s)' % letters
		if not pieces:
			return '1'
		return pieces


class CycleCount(object):
	"""A count of cycles of each length in a permutation's cycle decomposition."""
	def __init__(self, cyc_decomp):
		self.count = cl.Counter(len(cycle) for cycle in cyc_decomp.cycles)
		self.perm = cyc_decomp.perm
	
	def __getitem__(self, i):
		return self.count[i]

	def __iter__(self):
		return (self[i] for i in xrange(2, max(self.count) + 1))
	
	def __eq__(self, obj):
		if obj.__class__ != self.__class__:
			return False
		return all(c1 == c2 for c1, c2 in it.izip(self, obj))
			
	def __hash__(self):
		return hash(tuple(self))
	
	def __repr__(self):
		return repr(tuple(self))


def add_elements(elt, new, group):
	"""Generate new permutations to add to a group."""
	computed = set()
	for n in new:
		new_elt = Permutation(elt.of(n))
		if new_elt not in group:
			computed.add(new_elt)
			group.add(new_elt)
	return computed


def generate_group(gens):
	"""The group generated by a collection of permutations."""
	new, group = set(gens), set(gens)
	while(len(new)) > 0:
		computed = set()
		for elt in gens:
			computed |= add_elements(elt, new, group)
		new = computed
	return group


@lru_cache
def cyclic_group(elt):
	"""The cyclic group generated by elt."""
	group = {elt}
	g = Permutation(elt.of(elt))
	while g not in group:
		group.add(g)
		g = Permutation(elt.of(g))
	return group


def get_fingerprint(group):
	"""A histogram of cycle counts of permutations in a group."""
	return cl.Counter(g.cycle_decomposition.count for g in group)



