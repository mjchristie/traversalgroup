"""
Author: Matt Christie, 2016

Test to make sure that the priority queue functions as it should.
"""

import sys
import json
import logging
import random as r
import itertools as it

from priority_queue import PriorityQueue


bound = 2 ** 64
max_print = 15
insert_prob = 0.75
logging.basicConfig(level=logging.DEBUG)


def insert(pq):
	"""Randomly insert an integer into the priority queue."""
	i = r.randint(0, bound-1)
	pq.put(i)
	logging.info("insert %s", i)


def delete(pq):
	"""Randomly delete an element from the priority queue."""
	if not pq.empty():
		n = len(pq.heap.items)
		index = r.randint(1, n-1)
		deleted = pq.delete(index)
		logging.info("delete %s, got %s", index, deleted)


def insert_delete(pq, num_actions):
	"""Perform a random sequence of inserts/updates on the priority queue."""
	for _ in xrange(num_actions):
		p = r.random()
		action = insert if p < insert_prob else delete
		action(pq)


def log_items(items):
	"""Log items if there are few enough to be printed."""
	if len(items) < max_print:
		logging.info("ITEMS : %s", json.dumps(items))


def trial(trial_no, num_actions):
    """Perform one test run of the priority queue."""
	logging.info("Trial %s", trial_no)
	pq = PriorityQueue()
	insert_delete(pq, int(num_actions))
	items = []
	while not pq.empty():
		items.append(pq.get())
	if len(items) < 2:
		logging.info("Order is trivially preserved; fewer than 2 items.")
	preserved = True
	for i1, i2 in it.izip(items, items[1:]):
		if i1 >= i2:
			preserved = False
			break
	logging.info("Order%s preserved.", {True: "", False: " not"}[preserved])
	log_items(items)


def main(num_trials, num_actions):
    """Test the priority queue."""
	for i in xrange(int(num_trials)):
		trial(i+1, int(num_actions))


if __name__ == '__main__':
	main(*sys.argv[1:])
		



