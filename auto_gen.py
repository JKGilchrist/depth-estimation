from collection import Collection

import os
import sys
import random
    
if __name__ == "__main__":

    if not os.path.isdir("saves"):
        os.mkdir("saves")

    lst = os.listdir('assets')

    if len(sys.argv)  >= 2:
        lst = [sys.argv[1]]

    if len(sys.argv)  >= 3:
        mod_img_ind = int(sys.argv[2])
    else:
        mod_img_ind = random.randint(0, 2)

    for y in lst:
        lefts = os.listdir('assets/' + y + '/cameraLeft')
        centers = os.listdir('assets/' + y + '/cameraCenter')
        rights = os.listdir('assets/' + y + '/cameraRight')

        for left, center, right in zip(lefts, centers, rights):
            
            if not os.path.isdir("saves/logs"):
                os.mkdir("saves/logs")
            
            if not os.path.isdir("saves/generated"):
                os.mkdir("saves/generated")

            f = open("saves/logs/" + left[:-3] + "txt", 'w')
            sys.stdout = f
            left = y + '/cameraLeft/' + left
            center = y + '/cameraCenter/' + center
            right = y + '/cameraRight/' + right
            coll = Collection( left, center, right)
            mod_img = [left, center, right][mod_img_ind]
            coll.get_depth_img(mod_img, True, False)

            f.close()

