"""
Author: Matt Christie, 2015-2016

Print out a pictorial representation of a connected
graph's traversal permutations.
"""

import os
import sys
import json
import argparse
import random as r
import itertools as it
import collections as cl

from PIL import Image

import randobj
import serialize as srz


Color = cl.namedtuple('Color', ['r', 'g', 'b'])


def color_maker(start_color, act_color):
    """A function that makes a color from an index."""
    
    start, act = start_color, act_color
    
    def get_color(i):
        """The ith color."""
        values = ((s_val + i * a_val) % 256 for s_val, a_val in zip(start, act))
        return Color(*values)
    
    return get_color


def color_assigner(start_color, act_color, nodes):
    """A function that assigns a color to a node."""
    
    get_color = color_maker(start_color, act_color)
    colors = {node: get_color(i) for i, node in enumerate(nodes)}
    
    def assign_color(node):
        """The node's color."""
        return colors[node]
    
    return assign_color


def cell_printer(pixels, cell_length):
    """A function that prints a cell of the picture."""
    
    def print_cell(c, xcell, ycell):
        """Print a cell of the picture."""
        xvals = xrange(xcell * cell_length, (xcell + 1) * cell_length)
        yvals = xrange(ycell * cell_length, (ycell + 1) * cell_length)
        for x, y in it.product(xvals, yvals):
            pixels[x, y] = c
    
    return print_cell


def graph_printer(algorithm, cell_length, show=''):
    """A function that prints a picture of a graph's traversal sequences."""

    def print_graph(graph, start_color, act_color, filename=''):
        """Print a picture of a graph's traversal sequences."""
        
        traverse = getattr(graph, algorithm)
        
        # Make color-assigning function
        nodes = sorted(graph.nodes)
        color = color_assigner(start_color, act_color, nodes)
        
        # Initialize image
        side_length = cell_length * len(nodes)
        img = Image.new('RGB', (side_length, side_length), 'black')
        pixels = img.load()
        
        # Make cell-printing function
        print_cell = cell_printer(pixels, cell_length)
        
        # Fill in image
        for ycell, start_node in enumerate(nodes):
            for xcell, node in enumerate(traverse(start_node)):
                print_cell(color(node), xcell, ycell) 
        if show:
            img.show()
        if filename and type(filename) in {str, unicode}:
            img.save(filename)
    
    return print_graph


def filename_maker(directory, file_type):
    """A function that names the picture file."""
    
    if not os.path.exists(directory):
        os.makedirs(directory)

    def make_filename(i, start_color, act_color):
        """Make the filename for the picture."""
        start = '%s.%s.%s' % start_color
        act = '%s.%s.%s' % act_color
        kwargs = {'id': i, 'start': start, 'act': act, 'type': file_type}
        filename = 'G{id}_{start}_{act}.{type}'.format(**kwargs)
        return os.path.join(directory, filename)
    
    return make_filename


def make_color(color_vals):
    """Make a color from a list of values."""
    return Color(*color_vals)


def main(directory, algorithm, file_type='png',
         num_imgs=1, num_nodes=10, cell_length=10,
         start_color=[0, 0, 0], act_color=[25, 25, 25]):
    """Print a picture of a graph's traversal permutations."""
    
    start_color, act_color = [make_color(c) for c in (start_color, act_color)]
    nodes = range(1, num_nodes + 1)
    make_filename = filename_maker(directory, file_type)
    print_graph = graph_printer(algorithm, cell_length)
    
    for i in xrange(num_imgs):
        G = randobj.random_connected_graph(nodes)
        filename = make_filename(i, start_color, act_color)
        print_graph(G, start_color, act_color, filename=filename)


if __name__ == '__main__':
    desc = "Make a picture of a graph's traversal permutations."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('file', metavar='config-file',
                        type=file, default=file('config.json'),
                        help='JSON configuration file')
    
    kwargs = json.load(parser.parse_args().file)
    main(**kwargs)









            
    
