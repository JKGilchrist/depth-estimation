from collection import Collection

import sys
import os
import random

#args: img_type start to_save to_display
if __name__ == "__main__":
    
    if not os.path.isdir("saves"):
        os.mkdir("saves")

    num_args = len(sys.argv)

    if num_args >= 2:
        img_type = sys.argv[1]

    else:
        img_types = os.listdir('assets')
        r = random.randint(0, len(img_types) - 1)
        img_type = img_types[r]

    if num_args >= 3:
        img_index = int(sys.argv[2])

    else:
        img_index = random.randint(0, len(os.listdir('assets/' + img_type + "/cameraLeft/")) - 1)
    
    if num_args >= 4:
        mod_img_ind = int(sys.argv[3])
    else:
        mod_img_ind = random.randint(0, 1)

    if num_args >= 5:

        to_save = str(sys.argv[4]) == "True"
    else:
        to_save = False
    
    if num_args >= 6:
        display = str(sys.argv[5]) == "True"
    else:
        display = True



    if to_save and not os.path.isdir("saves/generated"):
        os.mkdir("saves/generated")


    file_name = os.listdir('assets/' + img_type + "/cameraLeft/")[img_index]
    left = img_type + "/cameraLeft/" + file_name
        
    file_name = os.listdir('assets/' + img_type + "/cameraRight/")[img_index]
    right = img_type + "/cameraRight/" + file_name

    mod_img = [left, right][mod_img_ind]

    print("\nimg_type: " + img_type, "\tindex: "+ str(img_index), "\tmodifying: "+ str(mod_img_ind), "\tsaving: " +  str(to_save), "\t  displaying: " + str(display), "\n")
    print(left)
    print(right)
    coll = Collection(left, right)
    coll.determine_colour_order()

    #coll.assign_shifts()
    #coll.get_depth_img(mod_img, to_save, display)
    