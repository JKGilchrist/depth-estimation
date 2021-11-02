from os import name
from shape import Shape
from helper import get_name, equal, name_convert, get_useful_pairs, get_two_dist, get_dist, get_readable_name

import matplotlib.pyplot as plt
import numpy as np
import copy
import math
import sys

class Image:
    """
    This class stores the images in a workable-manner (for Python) and functions related to their manipulation. 
    It additionally stores the subshapes identified in the image and their data
    """

    def __init__(self, shape_url : str, colours = {}):
        print("Generating image from " + shape_url)
        
        self.shape_url = shape_url
        self.shape_img = np.array(plt.imread(shape_url), dtype = np.uint8) # 3d array: rows, columns, values (rgba)

        if colours != {} :
            self.colours = colours
        else:
            self.colours = self.__get_colours()
        
        self.shapes = self.__get_shapes()
        print("Image processing complete\n")



    # Determines shape colours
    def __get_colours(self):
        print("\tDetermining shape colours")
        self.colours = {}
        
        hori_skip = math.ceil(self.shape_img.shape[1] * 0.01)
        vert_skip = math.ceil(self.shape_img.shape[0] * 0.01)

        vert_range = len(self.shape_img) - vert_skip
        
        row_index = 0
        col_index = 0

        while row_index < self.shape_img.shape[0] - vert_skip:
            cur_pix = self.shape_img[row_index][col_index]
            next_hori = self.shape_img[row_index][col_index + hori_skip]
            next_vert = self.shape_img[row_index + vert_skip][col_index]

            if equal(cur_pix, next_hori) and equal(cur_pix, next_vert):
                name = get_name(cur_pix)
                self.colours[name] = cur_pix
                col_index = col_index + vert_skip
            
            else:
                col_index = col_index + 1
            
            if col_index >= self.shape_img.shape[1] - hori_skip:
                
                if sys.stdout.isatty():
                    print("\t\tprogress: " + str(int(row_index / vert_range * 100)) + "%", end = "\r")
                col_index = 0
                row_index = row_index + 1
        print("\t\tprogress: 100%")
        return self.colours


    # Calculates all shapes within the image
    def __get_shapes(self):
        print("\tDetermining shape information")
        self.shapes = {}

        count = 0
        for colour in self.colours:
            if sys.stdout.isatty():
                print("\t\tprocessing shape: " + str(count) + "/"+ str(len(self.colours) - 1), end = "\r")

            self.shapes[colour] = Shape(self.shape_img, self.colours[colour], self.colours)
            count += 1

        print("\t\tprocessing shape: {}/{}".format(str(len(self.colours) - 1), str(len(self.colours) - 1)))
        return self.shapes


    # Used to create depth map image for displaying/saving
    def generate_mod_image( self, combos, img_num):

        # Create copy of image to modify
        mod_img = copy.deepcopy(self.shape_img)

        masks = {} # creates [[1,0,0,0...], ...] indicating if pixel is correct colour or not and ensures that if there already is a grey in img, its colour replacement can't get mixed up with another already replaced w the same exact colour
        for colour in combos:
            masks[colour] = np.all(mod_img == self.colours[colour], axis = -1 )
        
        for colour in combos:
            if type(combos[colour]["depth"]) != list:
                print("\tReplacing " + name_convert[colour] + ", " + colour + ", with calculated depth", combos[colour]["depth"])
                new_colour = [combos[colour]["depth"], combos[colour]["depth"], combos[colour]["depth"], 255]
                
                for row_i in range(self.shapes[colour].bounding_box["rows"]["top-most"], self.shapes[colour].bounding_box["rows"]["bottom-most"]):
                    for col_i in range(self.shapes[colour].bounding_box["columns"]["left-most"], self.shapes[colour].bounding_box["columns"]["right-most"]):
                        if masks[colour][row_i][col_i]:
                            mod_img[row_i][col_i] = new_colour 

            else: #
                print(combos[colour]["depth"][:20]) #list of lists (one per row of matching image) of lists of [ext_colour, (row_num, (col in img0, img1)), shift value, edge type (lrft/right) ] 
                                               # left edge type means it's left edge of that colour, with ext_colour to the left and var colour to the right

                #If there's any missed rows at the start, copy the first known and use that. TODO - could have it check the first few to see if they're trending one way or another to more accurately fill in the initial rows
                while combos[colour]["depth"][0][0][1][0] > self.shapes[colour].bounding_box["rows"]["top-most"]:
                    new_entry = [[y[0], (y[1][0] - 1, y[1][1]), y[2], y[3]] for y in combos[colour]["depth"][0] ]
                    combos[colour]["depth"] = [new_entry] + combos[colour]["depth"]
                    print(combos[colour]["depth"][0])
                
                #Same thing but with the bottom
                while combos[colour]["depth"][-1][0][1][0] < self.shapes[colour].bounding_box["rows"]["bottom-most"]:
                    new_entry = [[y[0], (y[1][0] + 1, y[1][1]), y[2], y[3]] for y in combos[colour]["depth"][-1] ]
                    combos[colour]["depth"].append(new_entry)

                print(combos[colour]["depth"][:20]) 


                for row in combos[colour]["depth"]:
                    row_pointer = 0
                    col = 0
                    row_num = row[0][1][0]

                    while row_pointer != len(row):
                        side = row[row_pointer][-1]

                        if side == "right":
                            new_colour = [row[row_pointer][2], row[row_pointer][2], row[row_pointer][2], 255]
                            for col_i in range(col, row[row_pointer][1][1][img_num] + 1):
                                if masks[colour][row_num][col_i]:
                                    mod_img[row_num][col_i] = new_colour
                            row_pointer += 1
                        
                        else: #side == "left"
                            if row_pointer + 1 != len(row): #if there's another elem in list
                                if row[row_pointer + 1][-1] == "right": #If it's a right
                                    left_col, left_shift = row[row_pointer][1][1][img_num], row[row_pointer][2]
                                    right_col, right_shift = row[row_pointer + 1][1][1][img_num], row[row_pointer + 1][2]
                                    ratio = (right_shift - left_shift) / (right_col - left_col)
                                    lst = [left_shift]

                                    for i in range(left_col + 1, right_col + 1):
                                        tmp = math.ceil( left_shift + ratio * (i - left_col))
                                        lst.append(tmp)
                                    
                                    for i in range(left_col, right_col):
                                        if masks[colour][row_num][i]:
                                            new_colour = [lst[0], lst[0], lst[0], 255]
                                            mod_img[row_num][i] = new_colour
                                            lst.pop(0)
                                    #get its shift
                                    #get difference in cols
                                    #if spot gets colour, calc its shift value as relative to their shifts
                                    row_pointer += 2
                                    print

                                else: 
                                    next_col = row[row_pointer + 1][1][1][img_num]
                                    new_colour = [row[row_pointer][2], row[row_pointer][2], row[row_pointer][2], 255]
                                    for col_i in range(row[row_pointer][1][1][img_num], next_col):
                                        if masks[colour][row_num][col_i]:
                                            mod_img[row_num][col_i] = new_colour
                                    row_pointer += 1
                                    
                            else: #last elem of list
                                last_col = len(masks[colour][0])
                                new_colour = [row[row_pointer][2], row[row_pointer][2], row[row_pointer][2], 255]
                                for col_i in range(row[row_pointer][1][1][img_num], last_col):
                                        if masks[colour][row_num][col_i]:
                                            mod_img[row_num][col_i] = new_colour
                                row_pointer += 1


                            print
                        
                #print("Not doing", get_readable_name(colour))
        return mod_img


    def get_specific_edge(self, int_colour, ext_colour ):
        shape = self.shapes[int_colour]
        ans = shape.get_specific_edge(ext_colour)
        return ans


    def get_specific_gradient_status(self, int_colour):
        shape = self.shapes[int_colour]
        ans = shape.get_gradient_status()
        return ans

    def get_bg_stats(self):
        tracker = {colour : set() for colour in self.colours}
        for row_i in range(0, len(self.shape_img), 10):
            row_colours = set()
            for col_i in range(0, len(self.shape_img[0]), 10):
                if get_name(self.shape_img[row_i][col_i]) in self.colours:
                    row_colours.add(get_name(self.shape_img[row_i][col_i]))
            #print(row_colours)

            for colour_1 in row_colours:
                for colour_2 in row_colours:
                    if colour_1 != colour_2:
                        tracker[colour_1].add(colour_2)
                        #tracker[colour_2].add(colour_1)
        
        #get inverse of tracker, so every colour lists what other colour it could be bg with
        inverse = {colour : set() for colour in self.colours}
        for x in tracker:
            for colour in self.colours:
                if colour not in tracker[x] and colour != x:
                    inverse[x].add(colour)

        print(inverse)
        ans = {colour : None for colour in self.colours}

        for x in inverse:
            if not len(inverse[x]): #aka if it has no elems
                ans[x] = False
            elif len(inverse[x]) + 1 == len([x for x in inverse if len(inverse[x])]): #if one matches with all the others
                ans[x] = True
        return ans

    def get_filtered_trios(self, trios, combos):
        useable = []
        for trio in trios:
            print([get_readable_name(y) for y in trio])
            a = get_useful_pairs([ x for x in self.shapes[trio[0]].edges['left'].segments + self.shapes[trio[0]].edges['right'].segments if x.ext_colour == trio[1] or x.ext_colour == trio[2]]) #given segments w ext_colour being one of two other colours in trio
            b = get_useful_pairs([ x for x in self.shapes[trio[1]].edges['left'].segments + self.shapes[trio[1]].edges['right'].segments if x.ext_colour == trio[0] or x.ext_colour == trio[2]])
            c = get_useful_pairs([ x for x in self.shapes[trio[2]].edges['left'].segments + self.shapes[trio[2]].edges['right'].segments if x.ext_colour == trio[0] or x.ext_colour == trio[1]])
            
            gradient = False in [combos[colour]["max"] for colour in trio]
            useable += self.get_useable_pairs(a,b, trio[0], trio[1], gradient) #returns [[segs],[segs]]
            useable += self.get_useable_pairs(a,c, trio[0], trio[2], gradient)
            useable += self.get_useable_pairs(b,c, trio[1], trio[2], gradient)

            #print("US", useable)
        #print("RETURNING", useable)
        return useable
            



    def get_useable_pairs(self, a, b, a_colour, b_colour, is_gradient):
        useable = []
        pointer_a = len(a) -1
        pointer_b = len(b) -1
        
        while pointer_a >= 0 and pointer_b >= 0 and len(a) and len(b) and len(a) > pointer_a and len(b) > pointer_b:
            print("G", a, pointer_a)
            x = a[pointer_a]
            y = b[pointer_b]
            
            matching_a = [i for i in x if i.ext_colour == b_colour][0] #edge in a with ext_colour b
            matching_b = [i for i in y if i.ext_colour == a_colour][0] #edge in b with ext_colour a

            ans = get_two_dist(matching_a, matching_b)
            #print(ans)
            if is_gradient and ans[0] < 50 and ans[1] < 50:
                other_colour_a = [i for i in x if i.ext_colour != b_colour][0]
                other_colour_b = [i for i in y if i.ext_colour != a_colour][0]
                other_ans = get_dist(other_colour_a, other_colour_b)

                if other_ans < 50:
                    useable.append([x, y])
                    a.pop(pointer_a)
                    b.pop(pointer_b)
            
            elif not is_gradient:
                useable.append([x, y])
                a.pop(pointer_a)
                b.pop(pointer_b)

            if pointer_b > 0:
                pointer_b -= 1
            else:
                pointer_a -= 1
                pointer_b = len(b) -1

        return useable


