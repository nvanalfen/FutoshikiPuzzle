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
        self.numbers = None
        self.dim = None
    
    def read_grid(self, f_name):
        df = pd.read_csv(f_name, header=None)
        pre_grid = np.array(df)
        self.dim = int( (len(pre_grid)+1)/2 )                # Right now, the rows and columns between the rows and columns of numbers are places for the innequalities
        self.grid = np.repeat(None, self.dim*self.dim).reshape( (self.dim, self.dim) )
        self.numbers = [i+1 for i in range(self.dim)]
        
        # Fill in the valued boxes
        for outer_y in range(len(pre_grid)):
            for outer_x in range(len(pre_grid[outer_y])):
                
                if outer_x%2 == 0 and outer_y%2 == 0:
                    # This is a box in the actual puzzle
                    x = int( outer_x/2 )
                    y = int( outer_y/2 )
                    self.grid[y,x] = Box(self.dim)
                    self.grid[y,x].x = x
                    self.grid[y,x].y = y
                    self.grid[y,x].set_value( int(pre_grid[outer_y, outer_x]) )
        
        # Loop through and add the relations
        for outer_y in range(len(pre_grid)):
            for outer_x in range(len(pre_grid[outer_y])):
                if outer_x%2 != 0 and outer_y%2 == 0:
                    # This is a < or > between two boxes on the left and right
                    left_x = int( outer_x/2 )           # x index of the left value box
                    y = int( outer_y/2 )
                    if pre_grid[outer_y, outer_x] == "<":
                        self.grid[y, left_x].add_relation( left_x+1, y, "<" )
                        self.grid[y, left_x+1].add_relation( left_x, y, ">" )
                    elif pre_grid[outer_y, outer_x] == ">":
                        self.grid[y, left_x].add_relation( left_x+1, y, ">" )
                        self.grid[y, left_x+1].add_relation( left_x, y, "<" )
                elif outer_x%2 == 0 and outer_y%2 != 0:
                    # This is a < or > between two boxes above and below
                    upper_y = int( outer_y/2 )          # y index of the upper box
                    x = int( outer_x/2 )                # x index of both boxes
                    if pre_grid[outer_y, outer_x] == "<" or pre_grid[outer_y, outer_x] == "^":
                        self.grid[upper_y, x].add_relation( x, upper_y+1, "<" )
                        self.grid[upper_y+1, x].add_relation( x, upper_y, ">" )
                    elif pre_grid[outer_y, outer_x] == ">" or pre_grid[outer_y, outer_x] == "v":
                        self.grid[upper_y, x].add_relation( x, upper_y+1, ">" )
                        self.grid[upper_y+1, x].add_relation( x, upper_y, "<" )
    
    def apply_innequalities(self):
        for y in range(len(self.grid)):
            for x in range(len(self.grid[y])):
                keys = self.grid[y,x].relations.keys()
                for x2, y2 in keys:
                    self.grid[y,x].limit_possibilities( self.grid[y2, x2] )
                self.remove_possibilities(x, y)
    
    def remove_possibilities(self, x, y):
        # If the current location is not solved, there's nothing to remove
        if not self.grid[y,x].solved:
            return
        
        val = self.grid[y,x].value
        
        # Remove the possibility from all boxes in the same row
        for box in self.grid[y,:]:
            # Only check those boxes that haven't been solved to avoid infinite recursion
            if not box.solved:
                box.remove_possibility(val)
                if box.solved:
                    # Recursive call, if removing the possibility solves a box, remove this new solution from the appropriate possibilities
                    self.remove_possibilities(box.x, box.y)
        
        # Remove the possibility from all boxes in the same column
        for box in self.grid[:,x]:
            # Only check those boxes that haven't been solved to avoid infinite recursion
            if not box.solved:
                box.remove_possibility(val)
                if box.solved:
                    # Recursive call, if removing the possibility solves a box, remove this new solution from the appropriate possibilities
                    self.remove_possibilities(box.x, box.y)
    
    def all_singleton(self):
        changes = 0
        for i in range(self.dim):
            changes += self.singleton_row(i)
        for i in range(self.dim):
            changes += self.singleton_column(i)
        
        return changes
    
    # Find any potential values (in the possibilities) in the current row that only appear once
    def singleton_row(self, ind):
        changes = 0
        
        frequencies = {}                                #Frequencies of the various possibilities
        for num in self.numbers:
            frequencies[num] = 0
        
        # Check all the boxes in the row specified at ind and check their possibilities
        for box in self.grid[ind,:]:
            # For each possibility in the current box, add one to its frequency count
            for pot in box.possibilities:
                frequencies[pot] += 1
        
        # Now check the counts for each potential value
        for key in frequencies:
            # Because each row needs exactly one of each number, if a number only appears as a possibility
            # in a single box, it must go there
            if frequencies[key] == 1:
                for box in self.grid[ind,:]:
                    if key in box.possibilities:
                        box.set_value(key)
                        self.remove_possibilities(box.x, box.y)             # Clean up and remove the set value from the possibilities of other boxes
                        changes += 1                                        # Add to the change count
                        break
        
        return changes
    
    # Find any potential values in the current column that only appear once
    def singleton_column(self, ind):
        changes = 0
        
        frequencies = {}            #Frequencies of the various possibilities
        for num in self.numbers:
            frequencies[num] = 0
        
        # Check all the boxes in the column specified at ind and check their possibilities
        for box in self.grid[:,ind]:
            # For each possibility in the current box, add one to its frequency count
            for pot in box.possibilities:
                frequencies[pot] += 1
        
        # Now check the counts for each potential value
        for key in frequencies:
            # Because each column needs exactly one of each number, if a number only appears as a possibility
            # in a single box, it must go there
            if frequencies[key] == 1:
                for box in self.grid[:,ind]:
                    if key in box.possibilities:
                        box.set_value(key)
                        self.remove_possibilities(box.x, box.y)             # Clean up and remove the set value from the possibilities of other boxes
                        changes += 1                                        # Add to the change count
                        break
        
        return changes
    
    def get_remaining(self):
        total = 0
        for row in self.grid:
            for box in row:
                total += box.remaining
        return total
    
    def get_remaining_possibilities(self):
        total = 0
        for row in self.grid:
            for box in row:
                total += len(box.possibilities)
        return total
    
    def is_solved(self):
        solved = True
        for row in self.grid:
            for box in row:
                solved = solved and box.solved
        return solved
        
    def solve(self):
        changes = 1
        self.apply_innequalities()
        
        while not self.is_solved() and changes:
            
            changes = self.all_singleton()                      # Look for singleton possibilities
                
            # If none were found, update the equality check to accound for new values having been found
            if changes == 0:
                before = self.get_remaining_possibilities()  
                self.apply_innequalities()
                after = self.get_remaining_possibilities()
                changes = before-after
        
    def print_grid(self, relations=False):
        for y in range(len(self.grid)):
            row = self.grid[y]
            row_text = ""
            lower_text = ""
            for x in range(len(row)):
                row_text += str(row[x].value)+" "
                if (x,y+1) in row[x].relations:
                    lower_text += row[x].relations[(x,y+1)]
                else:
                    lower_text += " "
                lower_text += "   "
                if (x+1,y) in row[x].relations:
                    row_text += row[x].relations[(x+1,y)]+" "
                else:
                    row_text += "  "
            print(row_text)
            print(lower_text)

def test():
    a = FutoshikiPuzzle()
    a.read_grid("Book1.csv")
    a.solve()
    return a

def print_possibilites(puzzle):
    for row in puzzle.grid:
        print([ box.possibilities for box in row ])
                                       