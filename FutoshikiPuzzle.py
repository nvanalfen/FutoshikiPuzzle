# -*- coding: utf-8 -*-
"""
Created on Fri Oct  9 08:34:24 2020

@author: nvana
"""

import pandas as pd
import numpy as np

# A variation on the box class used in SudokuSolver
class Box:
    def __init__(self, dimensions):
        self.possibilities = set( [i+1 for i in range(dimensions)] )
        self.min_val = min(self.possibilities)
        self.max_val = dimensions
        self.value = 0
        self.solved = False
        self.remaining = 1
        self.x = -1
        self.y = -1
        
        self.relations = {}                         # dict from coordinate (of other box) to the strings ">" or "<" depending on the relationship
        
    # Sets the value in a box, marks it as solved, and clears the possibilities
    def set_value(self, value):
        self.value = value
        self.temporary = value
        if value >= self.min_val and value <= self.max_val:
            self.solved = True
            self.remaining = 0
            self.possibilities = set()
    
    # Removes a possibility from the set of possibilities
    # If only one possibility remains, set the value
    def remove_possibility(self, value):
        try:
            self.possibilities.remove(value)
            self.check_possibilities()
        except:
            pass
    
    # Checks the possibilities and if only one remains, set the value
    def check_possibilities(self):
        if len(self.possibilities) == 1:
            self.set_value(self.possibilities.pop())
    
    def add_relation(self, x, y, rel):
        self.relations[ (x,y) ] = rel
    
    def check_relation(self, box_b):
        # This check is only for two solved boxes
        if not self.solved or not box_b.solved:
            return True
        x_b = box_b.x
        y_b = box_b.y
        if (x_b, y_b) in self.relations and (self.x, self.y) in box_b.relations:
            if self.relations[ (x_b, y_b) ] == "<":
                return self.value < box_b.value
            elif self.relations[ (x_b, y_b) ] == ">":
                return self.value > box_b.value
        return True                                 # The relation is satisfied if they don't include each other

    def limit_possibilities(self, box_b, inner_call=False):
        if self.solved:
            return
        
        x_b = box_b.x
        y_b = box_b.y
        if (x_b, y_b) in self.relations and (self.x, self.y) in box_b.relations:
            if self.relations[ (x_b, y_b) ] == "<":
                if box_b.solved:
                    self.possibilities = set( [ s for s in self.possibilities if s < box_b.value ] )
                else:
                    # All elements of self.possibilities must be smaller than the largest element of b.possibilities
                    self.possibilities = set( [ s for s in self.possibilities if s < max(box_b.possibilities) ] )
            elif self.relations[ (x_b, y_b) ] == ">":
                if box_b.solved:
                    self.possibilities = set( [ s for s in self.possibilities if s > box_b.value ] )
                else:
                    # All elements of self.possibilities must be larger than the smallest element of b.possibilities
                    self.possibilities = set( [ s for s in self.possibilities if s > min(box_b.possibilities) ] )
        
        self.check_possibilities()
        
        if not inner_call:
            box_b.limit_possibilities(self, inner_call=True)

class FutoshikiPuzzle:
    def __init__(self):
        self.grid = None
    
    def read_grid(self, f_name):
        df = pd.read_csv(f_name, header=None)
        pre_grid = np.array(df)
        dim = int( (len(pre_grid)+1)/2 )                # Right now, the rows and columns between the rows and columns of numbers are places for the innequalities
        self.grid = np.repeat(None, dim*dim).reshape( (dim, dim) )
        
        # Fill in the valued boxes
        for outer_y in range(len(pre_grid)):
            for outer_x in range(len(pre_grid[outer_y])):
                
                if outer_x%2 == 0 and outer_y%2 == 0:
                    # This is a box in the actual puzzle
                    x = int( outer_x/2 )
                    y = int( outer_y/2 )
                    self.grid[y,x] = Box(dim)
                    self.grid[y,x].x = x
                    self.grid[y,x].y = y
                    self.grid[y,x].set_value( int(pre_grid[outer_y, outer_x]) )
        
        # Loop through and add the relations
        for outer_y in range(len(pre_grid)):
            for outer_x in range(len(pre_grid[outer_y])):
                if outer_x%2 == 0 and outer_y%2 != 0:
                    # This is a < or > between two boxes on the left and right
                    left_x = int( outer_x/2 )           # x index of the left value box
                    y = int( outer_y/2 )                # y index of the value box
                    if pre_grid[outer_y, outer_x] == "<":
                        self.grid[y, left_x].add_relation( left_x+1, y, "<" )
                        self.grid[y, left_x+1].add_relation( left_x, y, ">" )
                elif outer_x%2 != 0 and outer_y%2 == 0:
                    # This is a < or > between two boces above and below
                    pass
                        