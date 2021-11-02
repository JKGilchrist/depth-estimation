import numpy as np
import math
import pickle
import matplotlib.pyplot as plt
import copy

# Used in testing to facilitate understanding of what is happening, not relied upon for any calculations
name_convert = {
    '000-188-255' : "Blue" ,
    '000-000-255' : "Pure Blue" ,
    '000-228-255' : "Light Blue" ,
    '255-151-000' : "Orange" ,
    '255-125-000' : "Orange" ,
    '204-000-000' : "Red" ,
    '255-000-035' : "Red" ,
    '125-040-234' : "Purple" ,
    '134-000-142' : "Purple" ,
    '255-217-000' : "Yellow" ,
    '255-211-000' : "Yellow" ,
    '156-156-156' : "Grey" ,
    '238-086-092' : "Pink" ,
    '218-078-078' : "Reddish Pink" ,
    '000-186-000' : "Light green" ,
    '171-255-000' : "Light green" ,
    '027-137-027' : "Dark green" ,
    '000-074-008' : "Dark green" ,
    'None' : 'None'
}


# Returns True if two lists are identical
def equal(lst1, lst2):
    if len(lst1) == len(lst2):
        for i in range(len(lst1)):
            if lst1[i] != lst2[i]:
                return False
    else:
        return False

    return True

def get_readable_name(val):
    if type(val) == np.ndarray:
        val = get_name(val)
    elif type(val) != str:
        print("Broke get_readable_name:", type(val))

    return name_convert[val]

# Creates string to facilitate referencing different colours
def get_name(arr):
    i = str(arr)
    ii = ( i[1:4] + "-" + i[5:8] + "-" + i[9:12]).replace(" ", "0")
    return str(ii)


# takes 2 tuples of 2 points each
def get_overlap(ends_1, ends_2):
    start = max(ends_1[0][1], ends_2[0][1])
    end = min(ends_1[1][1], ends_2[1][1] )
    overlap = end - start

    return overlap > 0, overlap, start, end


# Calculates the depth based on angles of left and right image between two points and the difference between 
# For some reason needs to needs be scaled up
def slope_depth(current_depth, left_angle, right_angle, bottom_edge):
    bottom_edge = bottom_edge * 85
    left_angle = math.pi - left_angle
    top_angle = math.pi - left_angle - right_angle

    left_upper_edge = math.sin(left_angle) * bottom_edge / (math.sin(top_angle) + 0.0001)
    
    depth = round( left_upper_edge * math.sin(right_angle))
    return  current_depth + depth 



def calc_depth(disparity):
    return round(280 * 35 / disparity, 2)


# Calculates the depth based on the displacement between the column value given by the left and right images (may be midpoints or left/right edge)
def _calc_depth(left_val, right_val, img_center):
    #print(left_val, right_val)
    base = (2800) #28 cm
    focal = (350) #35 mm
    
    bit = 0.0001 #To ensure there's no dividing by 0

    if left_val < img_center:
        bottom_left_angle = math.pi - math.atan( focal / (img_center - left_val + bit) )
    else:
        bottom_left_angle = math.atan( focal / (left_val - img_center + bit) )
    
    if right_val > img_center:
        bottom_right_angle = math.pi - math.atan( focal / (right_val - img_center + bit) )
    else:
        bottom_right_angle = math.atan( focal / (img_center - right_val + bit) )

    top_angle = math.pi - bottom_left_angle - bottom_right_angle
    left_upper_edge = math.sin(bottom_right_angle) * base / (math.sin(top_angle) + bit)

    depth = abs(round(left_upper_edge * math.sin(bottom_left_angle) / (math.sin(90) + bit ) ))

    return depth

#Useful pairs of segments 
def get_useful_pairs(segments):
    #print("D", segments)
    useful = [] # [[A's seg w colour b near, A's seg w colour c]]
    if len(segments) > 1:
        colours = list(set([x.ext_colour for x in segments])) #gets the unique ext colours (2)
        #print("C", colours)
        colour_1 = [x for x in segments if x.ext_colour == colours[0]] #all segs of the one ext_colour
        colour_2 = [x for x in segments if x.ext_colour == colours[1]] #all segs of the other ext_colour
        for x in colour_1:
            for y in colour_2:
                if get_dist(x,y) < 50:
                    useful.append([x, y])

    return useful

#get shortest distance between two segments
def get_dist(x, y):
    dist_00 = math.hypot(x.ends[0][0] - y.ends[0][0], x.ends[0][1] - y.ends[0][1])
    dist_01 = math.hypot(x.ends[0][0] - y.ends[1][0], x.ends[0][1] - y.ends[1][1])
    dist_10 = math.hypot(x.ends[1][0] - y.ends[0][0], x.ends[1][1] - y.ends[0][1])
    dist_11 = math.hypot(x.ends[1][0] - y.ends[1][0], x.ends[1][1] - y.ends[1][1])
    return min(dist_00, dist_01, dist_10, dist_11)


#get two shortest distances between two segments
def get_two_dist(x, y):
    dist_00 = math.hypot(x.ends[0][0] - y.ends[0][0], x.ends[0][1] - y.ends[0][1])
    dist_01 = math.hypot(x.ends[0][0] - y.ends[1][0], x.ends[0][1] - y.ends[1][1])
    dist_10 = math.hypot(x.ends[1][0] - y.ends[0][0], x.ends[1][1] - y.ends[0][1])
    dist_11 = math.hypot(x.ends[1][0] - y.ends[1][0], x.ends[1][1] - y.ends[1][1])
    ans = sorted([dist_00, dist_01, dist_10, dist_11])
    return ans[:2]




def basic_trios_search(combos, colours):
    pointer_1, pointer_2, pointer_3 = 0, 1, 2
    trios = []

    flag = True
    while flag:
        
        a, b, c = colours[pointer_1], colours[pointer_2], colours[pointer_3]
        if a in combos[b] and b in combos[a] and c in combos[a] and c in combos[b]:
            trios.append(sorted([a, b, c]))
            #print("trio", get_readable_name(a), get_readable_name(b), get_readable_name(c))

        if pointer_3 + 1 != len(colours):
            pointer_3 += 1
        elif pointer_2 + 2 != len(colours):
            pointer_2 += 1
            pointer_3 = pointer_2 + 1
        elif pointer_1 + 3 != len(colours):
            pointer_1 += 1
            pointer_2 = pointer_1 + 1
            pointer_3 = pointer_2 + 1
        else:
            flag = False

    return trios

















































#UNUSED
def remove_duplicate_sublists(lst):
    pointer_1 = 0
    pointer_2 = 1

    while pointer_1 < len(lst) and pointer_2 < len(lst):
        
        results = []
        for x, y in zip(lst[pointer_1], lst[pointer_2]):
            results.append(x == y)
        
        if False in results:
            results = []
            if pointer_2 + 1 < len(lst):
                pointer_2 += 1
            else:
                pointer_1 += 1
                pointer_2 = pointer_1 + 1
        else:
            lst.pop(pointer_2)
    return lst
















# Method to retrieve closest similar colour around pixel. Unused as image's pixel clean-up is unused
def get_cardinals(shape_img, colours, row_index, col_index, check_len):
    cardinals = {}
    if row_index > -1 + check_len and get_name(shape_img[row_index - check_len][col_index]) in colours:
        cardinals["above"] = shape_img[row_index - check_len][col_index]

    if row_index < shape_img.shape[0] - check_len and get_name(shape_img[row_index + check_len][col_index]) in  colours:
        cardinals["below"] = shape_img[row_index + check_len][col_index]
    
    if col_index > -1 + check_len and get_name(shape_img[row_index][col_index - check_len]) in colours :
        cardinals["left"] = shape_img[row_index][col_index - check_len]
    if col_index < shape_img.shape[1] - check_len and get_name(shape_img[row_index][col_index + check_len]) in colours:
        cardinals["right"] = shape_img[row_index][col_index + check_len]

    if cardinals:
        min = -1
        pix_sum = sum(shape_img[row_index][col_index])
        for key in cardinals:
            if min == -1:
                min = key
            else:
                cur_diff = abs(pix_sum - sum(cardinals[min]))
                key_diff = abs(pix_sum - sum(cardinals[key]))
                if key_diff < cur_diff:
                    min = key
        return cardinals[min]
    else:
        return None


# Simpler method to just ensure a colour is correct. Unused as image's pixel clean-up is unused
def confirm_colour(shape_img, colours, row_index, col_index, check_len):
    if row_index > -1 + check_len and col_index > -1 + check_len and equal(shape_img[row_index - check_len][col_index - check_len], shape_img[row_index][col_index]):
        return True

    if row_index < shape_img.shape[0] - check_len and col_index > -1 + check_len and equal(shape_img[row_index + check_len][col_index - check_len], shape_img[row_index][col_index]):
        return True
    
    if row_index > -1 and col_index < shape_img.shape[1] - check_len and equal(shape_img[row_index - check_len][col_index + check_len], shape_img[row_index][col_index]):
        return True
    if row_index < shape_img.shape[0] - check_len and col_index < shape_img.shape[1] - check_len and equal(shape_img[row_index + check_len][col_index + check_len], shape_img[row_index][col_index + check_len]):
        return True

    return False



# Saving/loading python-friendly files so everything doesn't have to be re-done with each execution
def save(objs, names):
    for (obj, name) in zip(objs, names):
        pickle.dump( obj, open( name, "wb" ) )

def load(name):
    return pickle.load(open(name, "rb"))

