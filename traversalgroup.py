"""
Author: Matt Christie, 2015-2016

Run trials that collect data on connected graphs and their
traversal groups, storing the results in a database.
"""

import os
import sys
import json
import math
import time
import sqlite3
import argparse
import datetime as dt
import collections as cl

import numpy as np
from sqlalchemy import create_engine, Table, MetaData, select, and_

import ddl
import randobj
import graph as g
import serialize as srz
import functions as fctn
from cache import lru_cache
from outtools import ProgressTallier


"""
TODO

1. Right now, the flow in Experiment.add_data is hardcoded. Ideally, would want
   to specify some dependencies of the data in a config file, then have the flow
   of the experiment look something like:
   
   dependencies = load_config_file()
   # handlers is a list of TableHandlers corresponding to tables in the database
   dependency_manager = DependencyManager(dependencies, handlers)
   for trial in trials:
       seed_data = {'initial': data, 'that_you': can_compute, 'without': the_database}
       dependency_manager.seed(seed_data)
       dependency_manager.add_data()

2. The experiment runs, but slowly. Analyzing the amounts of time spent in various
   functions, the most time is spent generating groups from permutations. Consider
   ways to improve this, maybe by precomputing/caching various groups and having a way
   to generate a group from a handful of subgroups that contain the generators
   being passed in. It's likely that, in the general case, computing the group that
   a set of permutations generate is not in the complexity class P.
"""


def cache_except_none(method):
    """Cache the return value of a method, except when the return value is None."""
    return lru_cache(method, include_nones=False)
    


class TableHandler(object):
    """The interface to a table in the database."""
    
    def __init__(self, engine, meta, conn):
        self.table = Table(self.name, meta, autoload=True, autoload_with=engine)
        self.conn = conn
    
    @cache_except_none
    def exists(self, **keys):
        """Determine if the object exists in the database."""
        eps = self.exists_params
        # keys = dict(keys)
        conditions = tuple(getattr(self.table.c, ep) == keys[ep] for ep in eps)
        s = select([self.table.c.id]).where(and_(*conditions))
        results = self.conn.execute(s)
        res = results.first()
        if res:
            table_id, = res
            return table_id
        return res
    
    def insert(self, obj):
        """Insert data into the database."""
        primary_keys = []
        for params in self.generate_data(obj):
            ins = self.table.insert().values(**params)
            result = self.conn.execute(ins)
            primary_keys.append(result.inserted_primary_key)
        return primary_keys


class GraphHandler(TableHandler):
    """The Graph table handler."""
    name = 'Graph'
    exists_params = ['id']
    
    def generate_data(self, obj):
        """Generate data to insert into the Graph table."""
        data = {
            'id': srz.graph_to_int(obj),
            'nodes': len(obj.nodes),
            'edges': len(obj.edges)
        }
        yield data


class PermGroupHandler(TableHandler):
    """The PermGroup table handler."""
    name = 'PermGroup'
    exists_params = ['repr']
    
    def generate_data(self, obj):
        """Generate data to insert into the PermGroup table."""
        yield obj


class PermutationHandler(TableHandler):
    """The Permutation table handler."""
    name = 'Permutation'
    exists_params = ['id']
    
    def generate_data(self, obj):
        """Generate data to insert into the Permutation table."""
        data = {
            'id': srz.perm_to_int(obj),
            'cycle_decomp': srz.seq_to_int(obj.cycle_decomposition.count)
        }
        yield data


class GroupClassHandler(TableHandler):
    """The GroupClass table handler."""
    name = 'GroupClass'
    exists_params = ['repr']
    
    def generate_data(self, obj):
        """Generate data to insert into the GroupClass table."""
        data = {
            'repr': srz.encode_group_class(obj),
            'size': sum(obj.values())
        }
        yield data


class HistogramHandler(TableHandler):
    """The Histogram table handler."""
    name = 'Histogram'
    exists_params = ['id', 'decomp', 'count']
    
    def generate_data(self, obj):
        """Generate data to insert into the Histogram table."""
        for cycle_decomp, count in obj['fingerprint'].iteritems():
            decomp = srz.seq_to_int(cycle_decomp)
            yield {'id': obj['id'], 'decomp': decomp, 'count': count}


class GroupElementHandler(TableHandler):
    """The GroupElement table handler."""
    name = 'GroupElement'
    exists_params = ['grp', 'elt']
    
    def generate_data(self, obj):
        """Generate data to insert into the GroupElement table."""
        for element in obj['elements']:
            yield {'grp': obj['id'], 'elt': srz.perm_to_int(element)}


class TrialHandler(TableHandler):
    """The Trial table handler."""
    name = 'Trial'
    exists_params = ['graph', 'nodes', 'method']
    
    def generate_data(self, obj):
        """Generate data to insert into the Trial table."""
        obj['datetime'] = time.time()
        yield obj


tables = [
    'Graph', 'PermGroup', 'Permutation',
    'GroupClass', 'Histogram', 'GroupElement', 'Trial'
]
handlers = {tbl: globals()['%sHandler' % tbl] for tbl in tables}


def generate_group(method, nodes):
    """G's traversal group on a subset of its nodes."""
    perms = {fctn.Permutation(list(method(node))) for node in nodes}
    return fctn.generate_group(perms)


def init_db(dbname):
    """Initialize a traversalgroup database."""
    with sqlite3.connect(dbname) as conn:
        conn.executescript(ddl.script)


class Experiment(object):
    """Store traversal groups of graphs on subsets of their nodes."""
    
    def __init__(self, config='config.json'):
        with open(config, 'r') as file_in:
            self.config = json.load(file_in)
        db = self.config['db']
        if not os.path.exists(db):
            init_db(db)
        engine = create_engine('sqlite:///%s' % db, echo=False)
        meta = MetaData()
        conn = engine.connect()
        self.handlers = {tbl: handlers[tbl](engine, meta, conn) for tbl in handlers}
    
    def run(self):
        """Run the experiment."""
        trials = 0
        progress = ProgressTallier(self.config['secs'], 0)
        min_trials = self.config['min_trials']
        while True:
            try:
                self.add_data()
                trials += 1
                progress.report(1)
            except KeyboardInterrupt:
                if trials < min_trials:
                    decision = ''
                    now = dt.datetime.now()
                    msg = '\n%s Only %s of %s trials have been run.\nQuit anyway? (y or n) > '
                    while decision == '' or decision[0] not in {'y', 'n'}:
                        decision = raw_input(msg % (now, trials, min_trials))
                    if decision[0] == 'y':
                        break
                else:
                    break
    
    def add_data(self):
        """Add data from a trial to the database."""
            
        # Graph
        G = self.random_connected_graph()
        graph_id = srz.graph_to_int(G)
        if not self.handlers['Graph'].exists(id=graph_id):
            self.handlers['Graph'].insert(G)
        
        # Subset of graph's nodes
        nodes = sorted(G.nodes)
        starting_nodes, node_encoding = randobj.random_subsequence(nodes, encoding=True)
        
        methods = {'bfs': G.bfs, 'dfs': G.dfs}
        for mtd, method in methods.iteritems():
        
            # PermGroup
            group = generate_group(method, starting_nodes)
            group_repr = srz.encode_objects(group, srz.perm_to_int)
            group_id = self.handlers['PermGroup'].exists(repr=group_repr)
            
            if group_id == None:
                
                # Permutation
                for perm in group:
                    perm_id = srz.perm_to_int(perm)
                    if self.handlers['Permutation'].exists(id=perm_id) == None:
                        self.handlers['Permutation'].insert(perm)
                
                # GroupClass
                group_class = fctn.get_fingerprint(group)
                group_class_repr = srz.encode_group_class(group_class)
                group_class_id = self.handlers['GroupClass'].exists(repr=group_class_repr)
                
                if group_class_id == None:
                
                    group_class_id = self.handlers['GroupClass'].insert(group_class)[0][0]
                    
                    # Histogram
                    histogram = {'id': group_class_id, 'fingerprint': group_class}
                    self.handlers['Histogram'].insert(histogram)
                
                group_data = {'repr': group_repr, 'cls': group_class_id}
                group_id = self.handlers['PermGroup'].insert(group_data)[0][0]
                
                # GroupElement
                self.handlers['GroupElement'].insert({'id': group_id, 'elements': group})
                
            # Trial
            trial_data = {
                'graph': graph_id, 'nodes': node_encoding,
                'method': mtd, 'grp': group_id
            }
            self.handlers['Trial'].insert(trial_data)

    def node_distribution(self):
        """A probability distribution on {min_n, min_n+1, ..., max_n}."""
        
        # The distribution is designed to ensure that min_n is picked at least
        # (# of connected graphs w/ min_n nodes) * (# of nonempty subsets of min_n elts)
        # times over a given number of trials with an approximate amount of certainty,
        # and that there is a sizable random sampling of connected graphs with k nodes,
        # min_n < k <= max_n.
        
        min_n = self.config['min_n']
        max_n = self.config['max_n']
        certainty = self.config['certainty']
        trials = self.config['min_trials']

        # Let P be the cartesian product of connected graphs and
        # nonempty subsets on min_n nodes
        connected_graphs = g.num_connected_graphs[min_n]
        nonempty_subsets = (1 << min_n) - 1
    
        # The size of P
        n = connected_graphs * nonempty_subsets
    
        # The probability of choosing a given element from P
        p = 1.0 / n
    
        # The event that an element e will be chosen at random from P only after
        # the kth attempt to do so is a geometric random variable; call it X. The
        # probability that e will have been chosen from P after k attempts have
        # been made is the cumulative distribution function of X, which is
        # P(X <= k) = 1 - (1 - p)^k.
    
        # c = 1 - (1 - p)^k
        # (1 - p)^k = 1 - c
        # k = log_{1 - p}(1 - c)
    
        k = math.ceil(math.log(1 - certainty) / math.log(1 - p))
        min_prob = float(k) / trials
    
        # Since the number of connected graphs on n nodes increases at least
        # exponentially with n, I want the probability of picking a connected
        # graph with n+1 nodes to be exponentially greater than the probability
        # of picking a connected graph with n nodes. This can be enforced by
        # requiring that q(1 + c + c^2 + ... + c^m-1) = 1 for some c,
        # where q = min_prob.

        q = min_prob

        # q^-1 = 1 + c + c^2 + ... + c^m-1
        # q^-1 = (1 - c^m)/(1 - c) (Partial sum of a geometric series)
        # q^-1(1 - c) = 1 - c^m
        # q^-1 - cq^-1 = 1 - c^m
        # c^m - (q^-1)c + (q^-1 - 1) = 0
        # Can find a root > 1 of mth degree polynomial in c numerically
    
        # Polynomial above has degree m, which has one more term than
        # the original polynomial on the RHS of the first line
        num_terms = ((max_n - min_n) + 1) + 1
        coeffs = [0] * num_terms
        coeffs[0] = 1
        coeffs[-2] = -(1.0 / q)
        coeffs[-1] = (1.0 / q) - 1
        roots = np.roots(coeffs)
        c = next(r.real for r in roots if r.real > 1.0 and r.imag == 0.0)
    
        distribution = [q * (c ** i) for i in xrange((max_n - min_n) + 1)]
        return distribution

    def random_connected_graph(self):
        """A random choice from the set of connected graphs with at least n nodes."""
        
        # A random connected graph can be chosen by first picking a random spanning tree,
        # then choosing a random subset of edges uniformly from the set of edges not
        # included in the tree.
        
        min_n = self.config['min_n']
        max_n = self.config['max_n']
        sizes = range(min_n, max_n + 1)
        
        distribution = self.node_distribution()
        size = randobj.pick(sizes, distribution)
        nodes = range(1, size + 1)
        return randobj.random_connected_graph(nodes)


def main(config='config.json'):
    """Run the experiment."""
    experiment = Experiment(config=config)
    experiment.run()


if __name__ == '__main__':
    desc = "Generate data on graphs and their traversal groups."
    parser = argparse.ArgumentParser(description=desc)
    help = "JSON configuration file"
    parser.add_argument('config', default='config.json', help=help)
    args = parser.parse_args()
    main(**vars(args))











