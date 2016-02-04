"""
Author: Matt Christie, 2015-2016

A heap-based priority queue.
"""

class Heap(object):
	"""A heap."""
	# https://en.wikipedia.org/wiki/Heap_(data_structure)

	def __init__(self, key=lambda item: item):
		self.items = ['Not used']
		self.eval = key
	
	def heapify_up(self, i):
		"""Restore heap property in tree above index i."""
		# Returns the least index of the last pair of elements reordered,
		# i if nothing was reordered.
		if i > 1:
			j = i/2
			if self.eval(self.items[i]) < self.eval(self.items[j]):
				tmp = self.items[i]
				self.items[i] = self.items[j]
				self.items[j] = tmp
				return self.heapify_up(j)
		return i
	
	def heapify_down(self, i):
		"""Restore heap property in tree below index i."""
		# Returns the greatest index of the last pair of elements reordered,
		# i if nothing was reordered.
		n = len(self.items)
		if 2 * i >= n:  # if i is a leaf node
			return i
		elif 2 * i + 1 < n:  # else if i has two children
			left, right = 2 * i, 2 * i + 1
			if self.eval(self.items[right]) < self.eval(self.items[left]):
				j = right
			else:
				j = left
		else:  # i only has a left child
			j = 2 * i
		# j is the least-valued child
		if self.eval(self.items[j]) < self.eval(self.items[i]):
			tmp = self.items[i]
			self.items[i] = self.items[j]
			self.items[j] = tmp
			return self.heapify_down(j)
		return i

class PriorityQueue(object):
	"""A priority queue."""
	# https://en.wikipedia.org/wiki/Priority_queue

	def __init__(self, key=lambda item: item):
		self.heap = Heap(key=key)
	
	def put(self, item):
		"""Add an element."""
		end = len(self.heap.items)
		self.heap.items.append(item)
		return self.heap.heapify_up(end)
	
	def peek(self):
		"""Look at the least element."""
		return self.heap.items[1]
	
	def get(self):
		"""Pop the least element."""
		top = self.heap.items[1]
		self.delete(1)
		return top		

	def delete(self, i):
		"""Delete the element at index i in the heap."""
		if i == len(self.heap.items) - 1:
			return self.heap.items.pop()
		deleted = self.heap.items[i]
		self.heap.items[i] = self.heap.items.pop()
		key = self.heap.eval
		if i == 1:
			self.heap.heapify_down(i)
		elif key(self.heap.items[i]) < key(self.heap.items[i/2]):
			self.heap.heapify_up(i)
		else:
			self.heap.heapify_down(i)
		return deleted
	
	def empty(self):
		"""Determine if the priority queue is empty."""
		return len(self.heap.items) == 1
	
	def __repr__(self):
		return "%s(%s)" % (self.__class__.__name__, repr(self.heap.items[1:]))
	
	def __getitem__(self, i):
		return self.heap.items[i]


def items(pq):
	"""Yield popped items from a priority queue in sorted order."""
	while not pq.empty():
		yield pq.get()





