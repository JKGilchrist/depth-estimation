from abc import get_cache_token
from image import Image
from helper import calc_depth, get_dist, get_readable_name, save, load, slope_depth, name_convert, get_name, basic_trios_search
from edge import compare_edges

import copy
import os
import math
import matplotlib.pyplot as plt
from PIL import Image as Img


class Collection:
    
    def __init__(self, left : str, right : str):

        # Create file names
        tmp_l = left.split("/")[-2] + "_" + left.split("/")[-1][:-4] + ".img"
        tmp_r = right.split("/")[-2] + "_" + right.split("/")[-1][:-4] + ".img"
        
        self.names = [tmp_l, tmp_r]

        # If they exist already, load, otherwise create them and save
        if os.path.exists("saves/" + tmp_l):
            print("Loading existing images")
            self.images = [load("saves/" +tmp_l), load("saves/" + tmp_r)]
            self.colours = self.images[0].colours
        else:
            right = Image( 'assets/' + right) 
            left = Image( 'assets/' + left , right.colours)
            
            self.images = [left, right]
            self.colours = self.images[0].colours

            save( [left, right] , ["saves/" + tmp_l, "saves/" + tmp_r] )



    def print_info(self):
        print("Current set-up of shapes")
        for shape in self.images[0].shapes:
            y = self.images[0].shapes[shape].get_all_avg_shifts()
            for x in y:
                print ("\n", get_readable_name(self.images[0].shapes[shape].colour) , x)
                for z in y[x]:
                    print(z)
                    #print(z[0], z[-1], ",", end = "\t")
                print()
            #print()
            #if get_readable_name( self.images[0].shapes[shape].colour) == 'Yellow':
            #    for seg in self.images[0].shapes[shape].edges['left'].segments:
            #        print( get_readable_name(seg.ext_colour), seg.pixels)
        

    #main function to start it all once initiated
    def determine_colour_order(self):
        self.calc_shifts() #assigns them to edges/segments
        self.combos = self.get_colour_combos()
        
        self.update_combos_grads()
        self.print_combos()
        
        self.update_combos_bgs()
        
        #self.print_info()
        #ans = self.images[0].get_specific_edge(list(self.colours.keys())[0], list(self.colours.keys())[1])
        #print(ans[0].avg_shift)
        
        self.transitive_combos()
        
        print("Initial")
        self.print_combos()
        
        self.trios_search()
        print("POst trios")
        self.print_combos()
        self.transitive_combos()
        print("post trans")
        self.print_combos()
        #raise
        self.duos_search()
        print("post duos")
        self.print_combos()

        self.transitive_combos()
        print("post trans")
        
        self.print_combos()
        
        self.uno_search()
        #self.print_info()
        self.gen_depth()
        self.convert_to_greyscale() 
        mod = self.images[0].generate_mod_image(self.combos, 0)
                          
        plt.imshow(mod)
        plt.show()

        
        
        
        
        
    def update_combos_bgs(self):
        print()
        dic = self.images[0].get_bg_stats()
        for colour in dic:
            if dic[colour] == True:
                self.combos[colour]["background"] = True
            if dic[colour] == False:
                self.combos[colour]["background"] = False

    #Gradient shapes cannot have maxes due to it varying 
    def update_combos_grads(self):
        grads = self.get_gradients()
        if grads:
            for grad in grads:
                self.combos[grad]['max'] = False
                self.combos[grad]['background'] = False #Gradient can't be bg



    def get_colour_combos(self):
        combos = {}

        for colour in self.colours:
            combos[colour] = {}
            combos[colour]['max'] = None #No known limit
            combos[colour]['background'] = None #Not known to be background

        for img in self.images:
            for shape in img.shapes:
                for edge in img.shapes[shape].edges:
                    for segment in img.shapes[shape].edges[edge].segments:
                        if segment.ext_colour == 'None':
                            combos[get_name(img.shapes[shape].edges[edge].int_colour)][segment.ext_colour] = [False, 0] #Ownership, shift amount
                        else:
                            if segment.ext_colour in combos[get_name(img.shapes[shape].edges[edge].int_colour)] :
                                #if abs(segment.avg_shift - combos[get_name(img.shapes[shape].edges[edge].int_colour)][segment.ext_colour][1]) > 10 :
                                #    print(get_readable_name( get_name(img.shapes[shape].edges[edge].int_colour) ), get_readable_name(segment.ext_colour))
                                #    print(segment.avg_shift, combos[get_name(img.shapes[shape].edges[edge].int_colour)][segment.ext_colour][1])
                                combos[get_name(img.shapes[shape].edges[edge].int_colour)][segment.ext_colour] = [None, max(segment.avg_shift , combos[get_name(img.shapes[shape].edges[edge].int_colour)][segment.ext_colour][1]) ] #Ownership, shift amount
                            
                            else:
                                combos[get_name(img.shapes[shape].edges[edge].int_colour)][segment.ext_colour] = [None, segment.avg_shift]

        
        return combos

    def trios_search(self):
        trios = basic_trios_search(self.combos, list(self.colours.keys())) #gets actual triple combos (colour A has edge with B and C, and colour B has edge with A and C)
        #print(trios)

        useable_segments = self.images[0].get_filtered_trios(trios, self.combos) #[  [[A's seg with colour B, seg with colour C], [B's seg with colour A, seg with colour C]] , [[],[]] ... ]
        #only images[0] as info is essentially duplicated across them -- could add merge of them later to be more thorough
        

        print(useable_segments)

        for useable_segment in useable_segments: # [[A's seg w B, A's seg w C],[B's seg w A, B's seg w C]]
            colours = set()
            [[colours.add(y.ext_colour) for y in x] for x in useable_segment]
            colours = list(colours)
            #print(colours)
            
            info = []  #[[one colour of edge, second colour of edge, avg_shift], ...]
            for pair in useable_segment:
                #print("W", [get_readable_name(x.ext_colour) for x in pair])
                ext_colour = [colour for colour in colours if colour not in [pair[0].ext_colour, pair[1].ext_colour]][0]
                
                for seg in pair:
                    lower = min(ext_colour, seg.ext_colour)
                    upper = max(ext_colour, seg.ext_colour)
                    info.append([lower, upper, seg.avg_shift])
            #print(" ")
            for x in info:
                print(get_readable_name( x[0]),get_readable_name( x[1]), x[2])
            #print("G")
            #Use info to form dict of avg_shift's per colour 
            dic = {k : [] for k in colours}
            for x in info:
                dic[x[0]].append(x[2])
                dic[x[1]].append(x[2])
            
            all_avgs = [math.floor( sum(dic[x]) / len(dic[x])) for x in dic]
            max_colour = [x for x in dic if math.floor(sum(dic[x])/len(dic[x])) == max(all_avgs)][0]
            #print(dic)
            #print("\nMAX:", get_readable_name(max_colour))
            limits = {k : -1 for k in colours if k != max_colour}
            #The limit for the non-max colours should be the max edge shift num between it and the max edge (1-2 data points)
            for x in [y for y in info if y[0] == max_colour or y[1] == max_colour]:
                other_colour = x[0] if x[0] != max_colour else x[1]
                limits[other_colour] = x[2] if limits[other_colour] == -1 else max(x[2], limits[other_colour])
            #print(limits)
            #Then, add info to combos, going with the lowest one to use
            for x in limits:
                #print(get_readable_name( x))
                if x in self.combos[max_colour].keys():
                    self.combos[max_colour][x] = [True, limits[x] if self.combos[max_colour][x][1] == None or limits[x] < self.combos[max_colour][x][1] else self.combos[max_colour][x][1] ]
                if max_colour in self.combos[x].keys():
                    self.combos[x][max_colour] = [False, limits[x] if self.combos[x][max_colour][1] == None or limits[x] < self.combos[x][max_colour][1] else self.combos[max_colour][x][1]]

                if self.combos[x]['max'] != False: #Indicates shape is gradient
                    self.combos[x]['max'] = limits[x] if self.combos[x]["max"] == None or limits[x] < self.combos[x]["max"] else self.combos[x]["max"]


            #And update segments to also have ownership indicated -- may be unneeded
            for pair in useable_segment:
                ext_colour = [colour for colour in colours if colour not in [pair[0].ext_colour, pair[1].ext_colour]][0]
                if ext_colour == max_colour:
                    for seg in pair:
                        seg.owner = True
                else:
                    for seg in pair:
                        if seg.ext_colour == max_colour:
                            seg.owner = False


    def print_combos(self):
        print("\n\nCombos")
        for key in self.combos:
            print(get_readable_name(key))
            for k in self.combos[key]:
                if k not in ['max', 'None', 'background', "depth"]:
                    print(get_readable_name(k) + ":", self.combos[key][k])
                else:
                    print(k + ":", self.combos[key][k])
            print()


    def calc_shifts(self):
        
        shapes = [x for x in self.images[0].shapes]
        edges = ['left', 'right']
        for shape in shapes:
            for edge in edges:
                print("\n\n?", get_readable_name( self.images[0].shapes[shape].colour),edge)
                img_0_edges = self.images[0].shapes[shape].edges[edge]
                img_1_edges = self.images[1].shapes[shape].edges[edge]
                compare_edges(img_0_edges, img_1_edges)
                #print("\n")
        
        


    def get_gradients(self):
        print("TTT")
        gradient_colours = []
        for colour in self.colours:
            ans = self.images[0].get_specific_gradient_status(colour) #It's the same for both imgs
            if ans:
                gradient_colours.append(colour)
        for x in gradient_colours:
            print("W", get_readable_name(x))
        return gradient_colours


    def transitive_combos (self):
        #print("in trans")
        made_change = True
        while made_change:
            #print("loop")
            made_change = False
            for key in self.combos:
                #print(get_readable_name(key), self.combos["255-000-035"]["max"])
                for k in self.combos[key]:
                    
                    if k not in ['max', 'None', 'background']: #k is another colour
                        #print("\t", get_readable_name(k))
                        #if a colour combo is unknown, but one colour can't possibly own it, due to shift being greater than its own max, it doesn't own it and the other does
                        if self.combos[key]['max'] not in [False, None]: #AKA is a number
                            #print("in")
                            if self.combos[key][k][0] == None and self.combos[key]['max'] < self.combos[key][k][1]:
                                self.combos[key][k][0] = False
                                made_change = True
                                if key in self.combos[k].keys():
                                    self.combos[k][key][0] = True

                            


                        #If you own edge1 and it's unknown if you own edge2 and edge1's shift > edge2, then you also own edge2
                        elif type(self.combos[key][k][0]) == bool:
                            for l in [x for x in self.combos[key] if x != k and x not in ["None", "max", "background"]]:
                                if self.combos[key][k][0] and self.combos[key][l][0] == None and self.combos[key][l][1] < self.combos[key][k][1]:
                                    #print("NO")
                                    self.combos[key][l][0] = True
                                    made_change = True
                                    if key in self.combos[l].keys():
                                        self.combos[l][key][0] = False
                                elif not self.combos[key][k][0] and self.combos[key][l][0] == None and self.combos[key][l][1] > self.combos[key][k][1]:
                                    self.combos[key][l][0] = False
                                    made_change = True
                                    if key in self.combos[l].keys():
                                        self.combos[l][key][0] = True
                        
                        #If you have unknown edge, and other colour's max is less than its shift, it's yours
                        elif self.combos[key][k][0] == None and type(self.combos[k]['max']) in [int, float] and self.combos[k]['max'] < self.combos[key][k][1]:
                            #print("\t\t\t\t\\tHIT!!!!", get_readable_name(key))
                            self.combos[key][k][0] = True
                            made_change = True
                            if key in self.combos[k].keys():
                                self.combos[k][key][0] = False
                                
                    # if you don't have a max but ought to
                    elif k == "max" and self.combos[key]['max'] == None:
                        shifts = [self.combos[key][x][1] for x in self.combos[key] if x not in ['max', 'None', "background"] and self.combos[key][x][0] == False]
                        if shifts:
                            self.combos[key]['max'] = min(shifts)
                            made_change = True
                    
                    #if you have a max value, it may impact ownership of edges
                    elif k == "max" and self.combos[key]['max'] != False: #Has a max value
                        shifts = [self.combos[key][x][1] for x in self.combos[key] if x not in ['max', 'None', "background"] and self.combos[key][x][0] == False]
                        if shifts and min(shifts) < self.combos[key]['max']:
                            self.combos[key]['max'] = min(shifts) 
                            made_change = True
                        
                    

                    elif k == "background" and self.combos[key][k] == None:
                        ownerships = [self.combos[key][x][0] for x in self.combos[key] if x not in ['max', 'None', 'background']]
                        if True in ownerships:
                            self.combos[key][k] = False
                            made_change = True
                        elif None not in ownerships: #aka colour doesnt own any
                            #print("IS BG", get_readable_name(key))
                            self.combos[key][k] = True
                            self.combos[key]['max'] = 0
                            for l in self.combos:
                                if key in self.combos[l].keys() and self.combos[l][key][0] != True: #the case when some shape has edge with background shape, but background shape doesn't recognize an edge with it
                                    #print("\t", get_readable_name(l))
                                    self.combos[l][key][0] = True
                            made_change = True
                    
                    elif k =="background" and self.combos[key][k] == True:
                        if self.combos[key]['max'] != 0:
                            self.combos[key]['max'] = 0
                            made_change = True
                        for x in self.combos[key]:
                            if x not in ['max', 'None', 'background'] and self.combos[key][x][0] == None:
                                self.combos[key][x][0] = False
                                made_change = True
                        for y in self.combos:
                            if key in self.combos[y].keys() and self.combos[y][key][0] == None:
                                self.combos[y][key][0] = True
                                made_change = True

                        #Otherwise it's still possible

            #Background check
            bgs = [x for x in self.combos if self.combos[x]["background"] == True]
            
            if len(bgs) != 2:
                potential_bgs = [x for x in self.combos if self.combos[x]["background"] == None]
                if len(bgs) == 0 and len(potential_bgs) == 2:
                    self.combos[potential_bgs[0]]["background"] = True
                    self.combos[potential_bgs[1]]["background"] = True
                    made_change = True
                elif len(bgs) == 1 and len(potential_bgs) == 1:
                    self.combos[potential_bgs[0]]["background"] = True
                    made_change = True
                    


    def duos_search(self):
        threshold = 1.00
        while threshold > 0.9:
            for key in self.combos:
                unknowns = [k for k in self.combos[key] if k not in ['None', 'max', "background"] and self.combos[key][k][0] == None]
                #Could check if other has an answer, but it shouldn't so 

                if len(unknowns) > 1:
                    pointer_1 = 0
                    pointer_2 = 1

                    while pointer_1 < len(unknowns) and pointer_2 < len(unknowns):
                        val_1 = self.combos[key][unknowns[pointer_1]][1]
                        val_2 = self.combos[key][unknowns[pointer_2]][1]
                        #print(val_1, val_2)
                        val_1, val_2 = max(val_1, val_2), min(val_1, val_2) #guarantees val_1 >= val_2
                        #print(val_1, val_2)
                        if math.floor(val_1 * threshold) <= val_2:
                            self.combos[key][unknowns[pointer_1]][0] = True
                            self.combos[key][unknowns[pointer_2]][0] = True
                            if key in self.combos[unknowns[pointer_1]].keys():
                                self.combos[unknowns[pointer_1]][key][0] = False
                            
                            if self.combos[unknowns[pointer_1]]['max'] != False:
                                self.combos[unknowns[pointer_1]]['max'] = min(self.combos[key][unknowns[pointer_1]][1], self.combos[unknowns[pointer_1]]['max'] )  if self.combos[unknowns[pointer_1]]['max'] != None else self.combos[key][unknowns[pointer_1]][1]

                            if key in self.combos[unknowns[pointer_2]].keys():
                                self.combos[unknowns[pointer_2]][key][0] = False
                            
                            if self.combos[unknowns[pointer_2]]['max'] != False:
                                self.combos[unknowns[pointer_2]]['max'] = min(self.combos[key][unknowns[pointer_2]][1], self.combos[unknowns[pointer_2]]['max'] )  if self.combos[unknowns[pointer_2]]['max'] != None else self.combos[key][unknowns[pointer_2]][1]


                            self.transitive_combos()


                        if pointer_2 < len(unknowns) - 1:
                            pointer_2 += 1
                        else:
                            pointer_1 += 1
                            pointer_2 = pointer_1 + 1
            threshold -= 0.01


    #What happens when there's a single unknown with no ability to combine info to determine its position
    def uno_search(self):
        self.background_check()
        self.print_combos()
        for colour in self.combos:
            evals = [self.combos[colour][x][0] for x in self.combos[colour] if x not in ["max", "background"]]
            if None in evals:
                print("\t\t",get_readable_name(colour),  "has failed")
            else:
                print(get_readable_name(colour),  "has passed")
        print()

    
    def background_check(self):
        bgs = [key for key in self.combos if self.combos[key]['background'] == True]

        if not bgs: #If no background has been found, we need to make an educated guess -- the one with the highest variance in its unknown edge's shifts
            
            var_dict = {}
            for key in self.combos:
                vals = [self.combos[key][k][1] for k in self.combos[key] if k not in ['max', 'None', 'background'] and self.combos[key][k][0] == None]

                if vals: #AKA it has 1+ unknown edges
                    var_dict[key] = max(vals) - min(vals)
            
            bg = [colour for colour in var_dict if var_dict[colour] == max(var_dict[x] for x in var_dict)][0] #gets key of var_dict w highest value entry / variance
            self.combos[bg]['background'] = True
            self.transitive_combos()
            bgs = [key for key in self.combos if self.combos[key]['background'] == True] #Update bgs

        if len(bgs) == 1: #only 1 background found
            potential_others = {y : [0, 0, self.combos[y]["max"]] for y in self.combos if self.combos[y]["background"] == None and y not in self.combos[bgs[0]].keys()  }
            print(potential_others)
            for colour in potential_others: #Number of not owned edges
                num = len([x for x in self.combos[colour] if x not in ["max", "background"] and self.combos[colour][x][0] == False])
                potential_others[colour][0] = num
            
            #Convert to ranked - Higher number == more likely to be background
            lst = sorted([y for y in potential_others], key = lambda x : potential_others[x][0])
            for i in range(len(lst)):
                potential_others[lst[i]][0] = i

            for colour in self.combos: #Number of occurrences in other colours' subcolours
                for sub_colour in self.combos[colour]:
                    if sub_colour in potential_others.keys():
                        potential_others[sub_colour][1] += 1
            
            #convert to ranked
            lst = sorted([y for y in potential_others], key = lambda x : potential_others[x][1])
            for i in range(len(lst)):
                potential_others[lst[i]][1] = i


            #Convert max values to ranked, lower max is more likely to be background
            lst = sorted([y for y in potential_others], key = lambda x : potential_others[x][2] if potential_others[x][2] != None else 1000, reverse=True)
            for i in range(len(lst)):
                potential_others[lst[i]][2] = i

            leader = sorted([y for y in potential_others], key = lambda x : sum(potential_others[x]), reverse=True)[0] #highest score == most likely to be bg
            
            self.combos[leader]['background'] = True
            self.transitive_combos()
            
            

                #if self.combos[key][k][0] == None: #if it has an unassigned edge
                #    vals = [x[1] for x in self.combos[key] if x not in ['max', 'None', 'background'] and self.combos[key][x][0] == False]
                #    print(vals)
                #    var_dict[key] = max(vals) - min(vals)
                #    
                    #print(get_readable_name(key), "has an unassigned edge!!")
        
        
        #what if 2 backgrounds haven't been found thus far
            #once they are, run transitive_combos
        
        #what if edge is between two colours 











    # Broadly manages getting depths for each shape using __gen_depth, handles ground/sky and converting to 0-255
    def __get_depths(self):
        # Get all depths
        depths = {}
        for shape in self.images[0].shapes:
            y = self.images[0].shapes[shape].get_all_avg_shifts()
            for x in y:
                print (name_convert[ get_name(self.images[0].shapes[shape].colour)] , x, self.images[0].shapes[shape].is_ground)
                for z in y[x]:
                    print(z)
            print()
            depths[shape] = self.__gen_depth(shape)
        # Look for sky / ground to assign their depths
        largest = max([depths[i][-1] for i in depths if depths[i]])
        smallest = min([depths[i][0] for i in depths if depths[i]])
        for key in depths:
            if depths[key] == []:
                if self.images[0].shapes[key].is_ground or self.images[1].shapes[key].is_ground:
                    if self.images[0].shapes[key].bounding_box["rows"]["top-most"] < self.images[0].shape_img.shape[0] * 0.2: # Sky
                        depths[key] = [math.ceil(largest * 1.05)]
                    else: # Ground
                        depths[key] = [math.ceil(smallest * 0.95)]

        # Remove smallest depth from all
        smallest = min([depths[i][0] for i in depths if depths[i]])
        for key in depths:
            if depths[key]:
                print(name_convert[key], depths[key])
                for y in range(len(depths[key])):
                    depths[key][y] = depths[key][y] - smallest
        
        # Convert to 0-255
        largest = max([depths[i][-1] for i in depths if depths[i]])
        for key in depths:
            print("Depth for " + name_convert[key] + " determined to be", depths[key])
            for i in range(len(depths[key])):
                x = depths[key][i]
                depths[key][i] = round( depths[key][i] / largest * 255)
                depths[key][i] = 255 - depths[key][i]
            print("\t\twhich converts to ", depths[key], "\n")
          
        return depths


    def gen_depth(self):
        
        bg1 = False

        for colour in self.combos:

            if self.combos[colour]["max"] != False and not self.combos[colour]["background"]: #Regular colour
                tmp = [self.combos[colour][y][1] for y in self.combos[colour] if y not in ["background", "max"] and self.combos[colour][y][0] == True]
                val = sum(tmp) / len(tmp)
                self.combos[colour]["depth"] = calc_depth(val)
                print(get_readable_name(colour), " is regular shape",self.combos[colour]["depth"]) 

            elif self.combos[colour]["max"] == False and not self.combos[colour]["background"]: #irregular colour
                print(get_readable_name(colour), " is irregular shape")
                self.combos[colour]["depth"] = self.get_complex_depth(colour)

            elif self.combos[colour]["background"] == True: #background colour

                if bg1: #have both background colours
                    print(get_readable_name(colour), " is background shape")
                    print(get_readable_name(bg1), " is background shape")
                    if self.images[0].shapes[colour].bounding_box["rows"]["top-most"] < self.images[0].shapes[bg1].bounding_box["rows"]["top-most"]: # < since first row of img is 1, and increases as you go down
                        self.combos[colour]["depth"] = 1000 #sky
                        self.combos[bg1]["depth"] = 0 #ground
                    else:
                        self.combos[colour]["depth"] = 0
                        self.combos[bg1]["depth"] = 1000

                else:
                    bg1 = colour



    def get_complex_depth(self, colour):
        left = self.get_column_vals(colour, 0)
        print()
        right = self.get_column_vals(colour, 1)
        print()

        max_shift = len(self.images[0].shape_img[0]) // 5 #max([self.combos[y]["max"] for y in self.combos if type(self.combos[y]["max"]) in [int, float] ]) * 1.5
        #print(left)
        #print(right)
        combined = []

        pointer_l = 0
        pointer_r = 0
        all_vals = []

        while pointer_l <= len(left) and pointer_r <= len(right):
            
            if pointer_l == len(left): #if at end of left list or left's row num is > right's row num
                pointer_r += 1
            elif pointer_r == len(right):
                pointer_l += 1

            elif right[pointer_r] == [] or (len(left[pointer_l]) and len(right[pointer_r]) and left[pointer_l][0][1] > right[pointer_r][0][1]):
                pointer_r += 1
                
            elif left[pointer_l] == [] or ( len(right[pointer_r]) and len(left[pointer_l]) and left[pointer_l][0][1] < right[pointer_r][0][1]):
                pointer_l += 1

            #elif left[pointer_l][0][1] == right[pointer_r][0][1]: #if they're on the same row
            else:
                combined.append([])

                for elem_l in left[pointer_l]: # (colour, row_i, col_i, left/right)
                    ind_r = 0
                    for i in range(ind_r, len(right[pointer_r])):
                        elem_r = right[pointer_r][i]

                        if elem_l[3] == elem_r[3] and elem_l[2] - elem_r[2] < max_shift and elem_l[2] - elem_r[2] > 0:
                            depth = calc_depth(elem_l[2] - elem_r[2])
                            combined[-1].append([elem_l[0], (elem_l[1], (elem_l[2], elem_r[2])), depth, elem_l[3]])
                            all_vals.append(depth)
                            ind_r = i + 1
                pointer_l += 1
                pointer_r += 1
        
        if max(all_vals) - min(all_vals) > min(all_vals) * 0.5:
            print(combined)
            depths = []
            for lst in combined:
                depths.append([x[2] for x in lst])
            print("\n\n\n\nDepths", depths)
            return combined
        else:
            all_vals.sort()
            return all_vals[len(all_vals) // 2]
            



            
    
    def get_column_vals(self, colour, img_num):
        top = self.images[img_num].shapes[colour].bounding_box["rows"]["top-most"]
        bottom = self.images[img_num].shapes[colour].bounding_box["rows"]["bottom-most"]
        left = self.images[img_num].shapes[colour].bounding_box["columns"]["left-most"]
        right = self.images[img_num].shapes[colour].bounding_box["columns"]["right-most"]
        lst = [] #each sublist rep a row in img

        row_i = top
        while row_i <= bottom:
            print( round((row_i - top) / (bottom - top) * 100 , 3), end="\r")
            lst.append([])
            col_i = left
            prev = None
            while col_i <= right:
                pix =  get_name(self.images[img_num].shape_img[row_i][col_i])
                if pix not in self.colours:
                    left_colour, right_colour = 0,0
                    col_l, col_r = 0, 0
                    for i in range(col_i - 1, -1, -1):
                        x = self.images[img_num].shape_img[row_i][i]

                        if get_name(x) in self.colours:
                            left_colour = get_name(x)
                            col_l = i
                            break

                    for i in range(col_i + 1, len(self.images[img_num].shape_img[row_i])):
                        x = self.images[img_num].shape_img[row_i][i]
                        if get_name(x) in self.colours:
                            right_colour = get_name(x)
                            col_r = i
                            break

                    if right_colour == colour and (prev == None or prev == "right"): #on left edge of shape:
                        if left_colour in self.combos[colour].keys() and self.combos[colour][left_colour][0]: #if we can calc its disparity and it's owned
                            lst[-1].append((left_colour, row_i, col_r, "left"))
                            #print(row_i, get_readable_name(left_colour), get_readable_name(right_colour), self.combos[colour][left_colour][1] )
                            col_i = col_r
                            prev = "left"
                    elif left_colour == colour and (prev == None or prev == "left"):
                        if right_colour in self.combos[colour].keys() and self.combos[colour][right_colour][0]:
                            lst[-1].append((right_colour, row_i, col_l, "right"))
                            col_i = col_l 
                            prev = "right"
                            #print(row_i, get_readable_name(left_colour), get_readable_name(right_colour), self.combos[colour][right_colour][1] )


                col_i += 1
            
            row_i += 1
        
        return lst
            


    def convert_to_greyscale(self):
        closest, furthest = False, False
        for colour in self.colours:
            if self.combos[colour]["background"]:
                continue
            elif type(self.combos[colour]["depth"]) != list:
                if not closest or closest > self.combos[colour]["depth"]:
                    closest = self.combos[colour]["depth"]
                if not furthest or furthest < self.combos[colour]["depth"]:
                    furthest = self.combos[colour]["depth"]
            else:
                for x in self.combos[colour]["depth"]:
                    for y in x:
                        if not closest or y[2] < closest:
                            closest = y[2]
                        if not furthest or y[2] > furthest:
                            furthest = y[2]
        
        ground = [x for x in self.combos if self.combos[x]["background"] == True and self.combos[x]["depth"] == 0][0]
        sky = [x for x in self.combos if self.combos[x]["background"] == True and self.combos[x]["depth"] == 1000][0]
        self.combos[ground]["depth"] = math.floor(0.95 * closest)
        self.combos[sky]["depth"] = math.floor(1.05 * furthest)
        closest = math.floor(0.95 * closest)
        furthest  = math.floor(1.05 * furthest - closest)
        print(closest, furthest)
        self.print_combos()

        for colour in self.colours:
            if type(self.combos[colour]["depth"]) != list:
                self.combos[colour]["depth"] = 255 - math.floor((self.combos[colour]["depth"] - closest) / furthest * 255)
                print(get_readable_name(colour),self.combos[colour]["depth"] )

            else:
                for x in self.combos[colour]["depth"]:
                    for y in x: #lists
                        y[2] = 255 - math.floor((y[2] - closest) / furthest * 255)
                
                print(get_readable_name(colour), self.combos[colour]["depth"])














    # Determines depth using displacement. Can give a singular answer that's the weighted median of all calculations or all of them
    def __get_flat_depth(self, shape, ranges, each_row = False):
        print(name_convert[shape])
        l_top = self.images[0].shapes[shape].bounding_box["rows"]["top-most"]
        r_top = self.images[1].shapes[shape].bounding_box["rows"]["top-most"]
        img_center = round(self.images[0].shape_img.shape[1] / 2)

        lst = [] # Using weighted median to determine depth value so it's most robust against outliers and values the depth determined using the midpoint more than using a single edge

        for rang in ranges:
            print(rang)
            if rang[2] == 2: # Owns both edges
                print("W")
                l_values = self.images[0].shapes[shape].centers[rang[0] - l_top: rang[1] - l_top]
                r_values = self.images[1].shapes[shape].centers[rang[0] - r_top: rang[1] - r_top]
                weight = 1

            else: # Only ones left (0) or right (1)
                print("X")
                l_values = [x[1] for x in self.images[0].shapes[shape].get_all_vert_edge(not rang[2])[rang[0] - l_top: rang[1] - l_top]]
                r_values = [x[1] for x in self.images[1].shapes[shape].get_all_vert_edge(not rang[2])[rang[0] - r_top: rang[1] - r_top]]
                weight = 0.25
            
            for l, r in zip(l_values, r_values):
                depth = calc_depth(l, r, img_center)
                lst.append((depth, weight))

        if each_row: # Used for gradient shapes so averaging doesn't occur
            lst = [x[0] for x in lst]
            return lst
        
        # Find weighted median
        lst.sort(key = lambda x : x[0])
        weight_sum = sum( x[1] for x in lst )
        adding = 0
        ind = 0
        while adding < round(weight_sum / 2):
            adding += lst[ind][1]
            ind += 1

        return lst[ind][0]



    # Controls delegation of depth estimation based on shape information
    # Returns the depth value(s) calculated
    # To adjust whether gradient shapes use slope or displacement to determine depths, change use_flat_depth
    def __gen_depth(self, shape):

        use_flat_depth = True # Used to toggle between which calculation to use for gradient shapes

        # Get ranges (and thus ownerships) for left image and right image
        l_left_segs = self.images[0].shapes[shape].edges["left"].segments
        l_right_segs = self.images[0].shapes[shape].edges["right"].segments
        l_ranges = get_ranges(l_left_segs, l_right_segs)
        
        r_left_segs = self.images[1].shapes[shape].edges["left"].segments
        r_right_segs = self.images[1].shapes[shape].edges["right"].segments
        r_ranges = get_ranges(r_left_segs, r_right_segs)
        
        # Combine ranges to determine valid ranges to use to perform calculations
        ranges = merge_ranges(l_ranges, r_ranges)
        
        # The case when the shape owns no edges - so the sky or ground
        if len(ranges) == 0:
            return []
        
        # Determine if shape is gradient
        gradient = False
        for seg in l_left_segs + l_right_segs + r_left_segs + r_right_segs:
            if seg.is_gradient:
                gradient = True
                break

        # Calculates depth using flat depth, so row-by-row, or slope, depending on bool use_flat_depth
        if gradient:
            if use_flat_depth:
                avgs = self.__get_flat_depth(shape, ranges)
                #avgs.reverse()
                return [avgs]
            else:
                avgs = self.__get_slope_depth(shape, ranges)
                return avgs

        # Calculates shape depth using flat depth, put into list as expected by calling function
        else:
            avg = self.__get_flat_depth(shape, ranges)
            return [avg]






























    # Manages edge ownership assignment
    # Part of initialization process
    def assign_shifts(self):
        print("Assigning edges to shapes")





        step = 0
        shapes = [x for x in self.images[0].shapes]
        edges = ['left', 'right']

        while step != 4:
            all_updates = set()

            if step == 0:
                print("\nstart step 0")
                for shape in shapes:
                    for edge in edges:
                        print("?", get_readable_name( self.images[0].shapes[shape].colour),edge)
                        img_0_edges = self.images[0].shapes[shape].edges[edge]
                        img_1_edges = self.images[1].shapes[shape].edges[edge]
                        vert = True
                        updates = compare_edges(img_0_edges, img_1_edges, vert)
                        print("\n")
                        if updates:
                            for update in updates:
                                all_updates.add(update)
                        
                print("End step 0\n")
                print("!!!!!!!!!!!!!!!!!!!!!!Perfect up to here!!!!!!!!!!!!!!! I think. All(ish) should be assigned reasonable shifts, no owners just yet")
                
                #raise()
            elif step == 1:
                print("\nstart step 1")
                for image in self.images:
                    updates = image.examine_shapes()
                    if updates:
                        print("GGG")
                        for update in updates:
                            all_updates.add(update)
                print("End step 1\n")
                #raise()
                        
            elif step == 2:
                raise()
                print("G")
                updates = self.images[0].find_additional_ownership_conclusions()
                if updates:
                    for update in updates:
                        all_updates.add(update)

                print("/G")



                #all_decisions = []
                #for image in self.images:
                #    decisions = image.ownership_decisions()
                #    if decisions:
                #        for decision in decisions:
                #            all_decisions.append(decision)

                #for decision in all_decisions:
                #    if all_decisions.count(decision) > 1:
                #        all_updates.add(decision)
                #        all_updates.add((decision[1], decision[0], False))

            elif step == 3:

                print("AT STEPP 3")

                for image in self.images:
                    updates = image.look_for_ground()
                    if updates:
                        for update in updates:
                            all_updates.add(update)

            if all_updates:
                #print("AT Updates")
                y= list(all_updates)
                for x in y:
                    print("update:", step, name_convert[ x[0]], name_convert[ x[1]], x[2])
                self.__update(y)
                    
            step += 1

    # Helper function for __assign_shifts. 
    # Sends updates to all images
    def __update(self, updates):
        if updates:
            for img in self.images:
                img.update_edges(updates)


    # Entry for depth calculation. Front-facing function that handles its orchestration
    def get_depth_img(self, url, to_save = False, display = True):
        
        tmp = url.split("/")[-2] + "_" +  url.split("/")[-1][:-4]
        
        if os.path.exists("saves/generated/" + tmp + ".img"):
            
            print("Depth image has already been generated")

            mod_img = load( "saves/generated/" + tmp + ".img" )
            to_save = False
        else:
            print("Generating depth image")
            
            print("Calculating depths")
            
            self.depths = self.__get_depths()

            if to_save or display:
                print("Creating modified image")
                
                index = self.names.index(tmp + ".img")
                
                mod_img = self.images[index].generate_mod_image(self.depths)
            
        if to_save:
            im = Img.fromarray(mod_img)
            im.save("saves/generated/" + tmp + ".png")
            
            save( [mod_img] , ["saves/generated/" +  tmp + ".img"])
            print("Modified image saved")

        if display:
            print("Displaying image")                    
            plt.imshow(mod_img)
            plt.show()




    # Determines depth using angles. Returns list as shape has varying depth
    def __get_slope_depth(self, shape, ranges):
        l_top = self.images[0].shapes[shape].bounding_box["rows"]["top-most"]
        r_top = self.images[1].shapes[shape].bounding_box["rows"]["top-most"]
        depths = [0]
        ranges = reversed(ranges)
        for rang in ranges:
            if rang[2] == 2:
                l_values = self.images[0].shapes[shape].centers[rang[0] - l_top: rang[1] - l_top]
                r_values = self.images[1].shapes[shape].centers[rang[0] - r_top: rang[1] - r_top]

            else:
                l_values = self.images[0].shapes[shape].get_all_vert_edge(not rang[2])[rang[0] - l_top: rang[1] - l_top]
                r_values = self.images[1].shapes[shape].get_all_vert_edge(not rang[2])[rang[0] - r_top: rang[1] - r_top]
            
            l_values.reverse() # Going from bottom of image to top
            r_values.reverse()

            left_angles = self.images[0].shapes[shape].get_angles(rang[1], rang[0], l_values)
            right_angles = self.images[1].shapes[shape].get_angles(rang[1], rang[0], r_values) 
            
            for i in range(len(left_angles)):
                diff = (left_angles[i][1][0] - right_angles[i][1][0]) - (left_angles[i][1][1] - right_angles[i][1][1]) # Bottom edge of triangle length
                depth = slope_depth(depths[-1], left_angles[i][0], right_angles[i][0], diff)
                depths.append(depth)

            
        return depths


        