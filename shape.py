from edge import Edge
from helper import equal, get_name, get_readable_name, name_convert

import math

class Shape:

    def __init__(self, img, colour, colours):
        self.img = img
        self.colour = colour
        self.colours = colours
        self.is_ground = None
        self.bounding_box = self.__get_bounding_box()
        self.shape = (len(self.img), len(self.img[0]))
        self.centers = self.__get_centers()
        self.edges = self.__get_defined_edges()


    def __str__(self):
        return str(self.bounding_box)


    def get_all_avg_shifts(self):
        dic = {}
        for edge in self.edges:
            dic[edge] = []
            for seg in self.edges[edge].segments:
                dic[edge].append((name_convert[ seg.ext_colour], "avg shift: " + str(seg.avg_shift), seg.ends, seg.owner))
        return dic


    # Generates edges of shape
    def __get_defined_edges(self):
        edges = {
            'left' : Edge( self.img, self.bounding_box, self.colour, self.get_all_vert_edge(True) , edge_name='left', colours = self.colours)   ,
            'right' : Edge( self.img, self.bounding_box, self.colour, self.get_all_vert_edge(False) , edge_name='right', colours = self.colours),
            }
        return edges


    # Returns bounding_box dictionary containing the shape's top-most row number, bottom-most row number, left-most column number, and right-most column number
    def __get_bounding_box(self):
        left_edge, right_edge, top_edge, bottom_edge  = -1, -1, -1, -1
        
        for row_i in range(self.img.shape[0]):
            for col_i in range(self.img.shape[1]):
                pix = self.img[row_i][col_i]

                if top_edge == -1 and equal(pix, self.colour): # Initial case and top edge
                    top_edge, bottom_edge = row_i, row_i
                    left_edge, right_edge = col_i, col_i
                elif equal(pix, self.colour):
                    if col_i < left_edge:
                        left_edge = col_i
                    if col_i > right_edge:
                        right_edge = col_i
                    if row_i > bottom_edge:
                        bottom_edge = row_i

        bounding_box = {
            "rows": { "top-most": top_edge, "bottom-most": bottom_edge },
            "columns": { "left-most": left_edge, "right-most": right_edge }
        }

        return bounding_box



    def get_specific_edge(self, ext_colour):
        ans_left = self.edges['left'].get_specific_seg(ext_colour)
        ans_right = self.edges['right'].get_specific_seg(ext_colour)
        return ans_left + ans_right


    def get_gradient_status(self):
        left = self.edges['left'].check_for_gradient()
        right = self.edges['right'].check_for_gradient()
        print( get_readable_name( self.colour), left, right)
        return left or right






    #TODO
    # Relies on idea that if a shape, has multiple segments of an edge, shared with different colours, with around the same displacement ( + or - 10%)
    # Then both are most likely owned by it 
    def examine_edges(self):
        updates = []

        for edge in self.edges:
            all_avgs = [segment.avg_shift for segment in self.edges[edge].segments]

            for segment in self.edges[edge].segments:
                avgs = [x for x in all_avgs]
                avgs.remove(segment.avg_shift)
                for x in avgs:
                    if x != None and segment.avg_shift != None and segment.owner == None and (x <= segment.avg_shift and math.floor( x *  1.1) >= segment.avg_shift or x >= segment.avg_shift and math.floor(x * 0.9) <= segment.avg_shift):
                        updates.append( ( segment.ext_colour, get_name(self.edges[edge].int_colour), False ) )
                        updates.append( (get_name(self.edges[edge].int_colour), segment.ext_colour, True ) )
        return updates






















    # Returns angles the slope between two points forms as well as the column values used, so displacement can be calculated
    def get_angles(self, start, stop, values):
        angles = []
        
        cur_row = start
        skip = 1

        for i in range(0, len(values) - skip, skip):
            y1, y2 = cur_row - skip, cur_row
            x1, x2 = values[i + skip], values[i]
            if x2 - x1 != 0:
                delta = round((y2 - y1) / (x2 - x1), 5) * -1 # Negated since the visually higher row has the lower row number
                angle = math.atan(delta)
                if angle < 0 :
                    angle += math.pi
            else:
                angle = math.pi / 2
            cols = (x2, x1) # (bottom point's col, top point's col)
            angles.append((angle, cols)) 
            cur_row -= skip
        return angles


    # Returns all column values of each row's midpoint of the shape
    def __get_centers(self):
        
        left_edge = self.get_all_vert_edge(True)
        right_edge = self.get_all_vert_edge(False)

        centers = []
        for x,y in zip(left_edge, right_edge):
            
            mid = round((x[1] + y[1]) / 2)
            centers.append(mid)
        return centers


    # Returns all col values of left or right edge of shape
    # Relies on shape not having any gaps horizontally
    def get_all_vert_edge(self, left = True):
        values = []
        if left:
            start, stop, step =  self.bounding_box["columns"]["left-most"],  self.bounding_box["columns"]["right-most"] + 1, 1
        else:
            start, stop, step =  self.bounding_box["columns"]["right-most"], self.bounding_box["columns"]["left-most"] - 1, - 1

        for row_index in range(self.bounding_box["rows"]["top-most"], self.bounding_box["rows"]["bottom-most"] + 1):
                for col_index in range(start, stop, step):
                    if equal(self.img[row_index][col_index], self.colour):
                        values.append((col_index, row_index)) # x, y values
                        break
        return values
    



    
