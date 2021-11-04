from collection import Collection

import sys
import os
import random

#args: img_type start to_save to_display
if __name__ == "__main__":
    
    if not os.path.isdir("saves"):
        os.mkdir("saves")

    #Args
    num_args = len(sys.argv)
    img_type = sys.argv[1] if num_args >= 2 else os.listdir('assets')[random.randint(0, len(os.listdir('assets')) - 1)]
    img_index = int(sys.argv[2]) if num_args >= 3 else random.randint(0, len(os.listdir('assets/' + img_type + "/cameraLeft/")) - 1)
    mod_img_ind = int(sys.argv[3]) if num_args >= 5 else random.randint(0, 1)
    to_save = str(sys.argv[4]) == "True" if num_args >= 5 else False
    display = str(sys.argv[5]) == "True" if num_args >= 6 else True


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
    