class Segment:

    def __init__(self, pixels, colour):

        self.pixels = pixels # [(col_index, row_index), ... ]
        self.ends = (pixels[0], pixels[-1])
        self.ext_colour = colour # colour of other side of edge
        if self.ext_colour == 'None': # if edge is edge of image itself, it's not owned by the shape
            self.avg_shift = False
            self.all_shifts = False
            self.is_gradient = False
            self.owner = False
        else:
            self.avg_shift = None # Indicates avg shift is unknown
            self.all_shifts = None
            self.is_gradient = None
            self.owner = None


    # Retrieves specified pixels
    #TODO broke?
    def get_pixels_in_range(self, start, stop):
        #print("in get pixels in range", start, stop) #324 404
        vals = [y[1] for y in self.pixels]
        #print(vals)
        start = vals.index(start)
        #print("G")
        stop = vals.index(stop)
        #print("GG")
        #print(start, stop) #46 -214
        #print()
        return self.pixels[start:stop]


