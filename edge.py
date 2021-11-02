from helper import equal, get_name, get_readable_name, get_overlap
from segment import Segment

import statistics


class Edge:
    
    def __init__(self, img, bounding_box, colour, values, edge_name, colours):
        self.img = img
        self.shape_bounding_box = bounding_box
        self.int_colour = colour # Colour of own shape
        self.edge_name = edge_name
        self.colours = colours
        self.segments = []
        self.__gen_edge(values)
        if self.segments:
            self.ends = (self.segments[0].ends[0], self.segments[-1].ends[1])


    #Values is list of tuples, representing coords of shape's edge pixels [(col_index, row_index), ()]
    def __gen_edge(self, values):
        
        #get list of ((col_index, row_index), opposing_colour)
        pixels = self.__add_colours_to_pixels(values)

        cur_colour = pixels[0][1]
        cur_pixs = [pixels[0][0]] # [(col_index, row_index), ... ]

        for pix in pixels[1:]:
            if equal(pix[1], cur_colour) and pix[0][1] == cur_pixs[-1][1] + 1 and abs(pix[0][0] - cur_pixs[-1][0]) < 300: #vert(/row) increases by 1 and no dramatic change in horizontal
                cur_pixs.append(pix[0])
            else:
                if len(cur_pixs) >= 3:
                    self.segments.append( Segment(cur_pixs, cur_colour) )
                cur_pixs = [pix[0]]
                cur_colour = pix[1]
        
        if len(cur_pixs) >= 3:
            self.segments.append( Segment(cur_pixs, cur_colour) )

    #Convert values into ((col_ind, row_ind), opposing_colour) for each edge pixel
    def __add_colours_to_pixels(self, values):
        lst = []
        for pixel in values:

            if self.edge_name == 'left':
                step = -1
                end = 0
            elif self.edge_name == 'right':
                step = 1
                end = self.img.shape[1]

            if self.edge_name == 'right' and pixel[0] < end - 2 or self.edge_name == 'left' and pixel[0] > end + 2:
                opposing_colour = get_name( self.img[pixel[1]][pixel[0] + step])
                count = 1
                
                for j in range(pixel[0] + step, end, step):
                    if opposing_colour in self.colours and get_name(self.img[pixel[1]][j]) == opposing_colour:
                        count += 1
                    else: 
                        opposing_colour = get_name(self.img[pixel[1]][j])
                        count = 1
                    
                    if count == 2:
                        break
                
                if count != 2:
                    opposing_colour = 'None'

            else:
                opposing_colour = 'None'
            
            lst.append((pixel, opposing_colour))
        return lst


    def get_specific_seg(self, ext_colour):
        ans = []
        for seg in self.segments:
            if seg.ext_colour == ext_colour:
                ans.append(seg)
        return ans
    

    def check_for_gradient(self):
        #If a seg is gradient, edge is gradient
        for seg in self.segments:
            if seg.is_gradient:
                print( get_readable_name( self.int_colour), "is grad1")
                return True
        
        # If a shape has multiple segments which steadily increase/decrease
        avg_shifts = []
        lens = []
        all = []
        for seg in self.segments:
            avg_shifts.append(seg.avg_shift)
            lens.append(len(seg.pixels))
            all.append(seg.all_shifts)
        diff = 0.25

        if len(avg_shifts) >= 3:
            for i in range(len(avg_shifts) - 2):
                a = avg_shifts[i]
                b = avg_shifts[i+1]
                c = avg_shifts[i+2]
                
                if a and b and c: #Probably should be more robust
                    if a < b and b < c and b - a < a * diff and c - b < a * diff or a > b and b > c and b - c < c * diff and a - b < c * diff:
                        print(get_readable_name( self.int_colour), "is grad2")
                        print(a, b, c)
                        print(lens)
                        print(all)
                        return True

        return False
        



def print_segs(segments):
    for seg in segments:
        print("\t", get_readable_name(seg.ext_colour), seg.ends[0][1],"-" , seg.ends[1][1], seg.avg_shift, seg.is_gradient)



#Assigns shift values to segments
# Segment.pixels = [(col_index, row_index), ... ]
def compare_edges(left_img_edge, right_img_edge ):

    print("img 0 before")
    print_segs(left_img_edge.segments)
    print("img 1 before")
    print_segs(right_img_edge.segments)
    
    for side in ['left', 'right']:
        indexes = [] #segments to be removed, since they've no counter-part to compare with
        initial_segs = left_img_edge.segments if side == 'left' else right_img_edge.segments

        for i in range(len(initial_segs)): 
            seg = initial_segs[i]

            matching = right_img_edge.segments if side == 'left' else left_img_edge.segments
            matching_segments = [y for y in matching if y.ext_colour == seg.ext_colour]
            
            if len(matching_segments) > 0 and seg.ext_colour != 'None':
                shifts = get_shifts(seg, matching_segments)

                if len(shifts) > 0:
                    seg.all_shifts = shifts
                    seg.avg_shift = statistics.median(shifts) # Median used due to it being robust against outlier values

                    if len(shifts) > 1:
                        me = round(statistics.mean(shifts),3)
                        me_min = round(me - min(shifts),3)
                        me_max = round( max(shifts) - me,3)
                        var = round(statistics.variance(shifts),3)
                        rang =  max(shifts) - min(shifts)

                        # If variance is large and mean is representative (the case when a shape is a gradient)
                        if var > rang * 3 and me_min < 0.6 * rang and me_max < 0.6 * rang:
                            #print("!!!!!!!!!!!!!!", var, rang, me_min, me_max)
                            seg.is_gradient = True
                            for matching in matching_segments:
                                matching.is_gradient = True
                        else:
                            seg.is_gradient = False
                    else:
                        seg.is_gradient = False

            elif len(matching_segments) == 0:
                indexes.append(i)
        
        #Remove those unmatchable segs
        indexes.reverse()    
        for i in indexes:
            left_img_edge.segments.pop(i) if side == 'left' else right_img_edge.segments.pop(i)


    #remove any still remaining segments that couldn't be calc'd
    left_img_edge.segments = [seg for seg in left_img_edge.segments if not (seg.avg_shift == None and seg.ext_colour != 'None')] 
    right_img_edge.segments = [seg for seg in right_img_edge.segments if not (seg.avg_shift == None and seg.ext_colour != 'None')]

    print("\nimg 0 after")
    print_segs(left_img_edge.segments)
    print("img 1 after")
    print_segs(right_img_edge.segments)

    #left_img_edge.check_for_gradient()

    
#Helper function for compare_edges
def get_shifts(initital_seg, matching_segs):
    shifts = []
    
    for matching_seg in matching_segs:
        start = max(initital_seg.ends[0][1], matching_seg.ends[0][1])
        end = min (initital_seg.ends[1][1], matching_seg.ends[1][1])

        if start < end and end - start > 0:
            initial_pixels = initital_seg.get_pixels_in_range(start, end)
            matching_pixels = matching_seg.get_pixels_in_range(start, end)

            for i in range(len(initial_pixels)):
                shifts.append(abs(initial_pixels[i][0] - matching_pixels[i][0]))
    return shifts
