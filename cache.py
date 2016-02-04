"""
Author: Matt Christie, 2015-2016

Cache function calls.
"""

import time

from priority_queue import PriorityQueue


def is_iterable(item):
	"""Determine if something is iterable."""
	try:
		it = iter(item)
		return True
	except TypeError:
		return False


def argument_key(args, kwargs):
	"""A function's arguments in hashable form."""
	return args, tuple(sorted(kwargs.iteritems()))


def memoized(func):
	"""Memoize a function with immutable arguments."""
	# Modeled after Python 3's functools.lru_cache with maxsize=None
	past_calls = {}
	def memoized_func(*args, **kwargs):
		ak = argument_key(args, kwargs)
		if ak not in past_calls:
			past_calls[ak] = func(*args, **kwargs)
		return past_calls[ak]
	return memoized_func


class LRUCache(object):
	"""A least-recently-used cache."""
	
	def __init__(self, maxsize=100):
		self.items = {}
		self.oldest = PriorityQueue(key=lambda item: item['timestamp'])
		self.maxsize = maxsize
		self.numitems = 0
	
	def insert(self, key, value):
		"""Insert a piece of data into the cache."""
		if self.numitems >= self.maxsize:
			throw_away = self.oldest.get()
			del self.items[throw_away['key']]
			self.numitems -= 1
		pq_data = {'key': key, 'timestamp': time.time()}
		self.items[key] = {
			'index': self.oldest.put(pq_data),
			'value': value
		}
		self.numitems += 1
	
	def update(self, key):
		"""Update the timestamp of a piece of data in the cache."""
		index = self.items[key]['index']
		self.oldest[index]['timestamp'] = time.time()
		self.oldest.heap.heapify_down(index)
	
	def remove(self, key):
		"""Remove a piece of data from the cache."""
		index = self.items[key]['index']
		thrown_away = self.oldest.delete(index)
		del self.items[key]
		self.numitems -= 1
	
	def __contains__(self, key):
		return key in self.items
	
	def __getitem__(self, key):
		return self.items[key]['value']


# Max number of elements that an LRUCache will hold.
# Consider making this a decorator argument.
cachesize = 720


def lru_cache(func, include_nones=True):
	"""Cache values of a function with immutable arguments."""
	cache = LRUCache(maxsize=cachesize)
	def cached(*args, **kwargs):
		key = argument_key(args, kwargs)
		if key in cache:
			cache.update(key)
			return cache[key]
		value = func(*args, **kwargs)
		if include_nones or value != None:
			cache.insert(key, value)
		return value
	return cached



