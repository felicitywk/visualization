# Implemented by: Hayk Aleksanyan
# based on the approach by Jonathan Feinberg, see http://static.mrfeinberg.com/bv_ch03.pdf

from PIL import Image
from PIL import ImageColor
from PIL import ImageFont
from PIL import ImageDraw

import math     # for sin, cos
import random   # used for random placement of the initial position of a word

import timeit   # for calculating running time (TESTING purposes only)

import numpy as np
import sys


import fileReader as FR
import spirals as SP
from Trees import Node
from Trees import Tree


def rectArea(r):
    #returns the area of the rectangle given in min-max coordinates (top-left bottom-right)
    return abs( (r[0] - r[2])*(r[1] - r[3]) )

def intersectionRect(r1, r2, shift1 = (0,0), shift2 = (0,0), extraSize = 3 ):
    """
     gets two 4-tuples of integers representing a rectangle in min,max coord-s
     optional params. @shifts can be used to move boxes on a larger canvas (2d plane)
                      @extraSize, forces the rectangles to stay away from each other by the given size (number of pixels)

     returns True if the rectangles intersect
    """

    if ((min(r1[0] - extraSize + shift1[0] , r1[2] + extraSize + shift1[0] ) > max( r2[0] - extraSize + shift2[0], r2[2] + extraSize + shift2[0] ) )
        or ( max(r1[0] - extraSize + shift1[0], r1[2] + extraSize + shift1[0] ) < min( r2[0] - extraSize + shift2[0], r2[2] + extraSize + shift2[0] ) ) ):
        return False

    if ((min(r1[1] - extraSize + shift1[1] , r1[3] + extraSize + shift1[1] ) > max( r2[1] - extraSize + shift2[1], r2[3] + extraSize + shift2[1]) )
        or ( max(r1[1] - extraSize + shift1[1], r1[3]  + extraSize + shift1[1] ) < min( r2[1] - extraSize + shift2[1], r2[3]+ extraSize + shift2[1] ) ) ):
        return False

    return True

def computeFontSize(words):
    #gets the words_ dictionary, i.e. the list of words, and their frequencies
    #returns the list of suggested fonts for each of them

    w_Font = []

    keys = list(words.keys())
    #the 1st key is the word, the 2nd is the frequency

    #we simply make the font size = count of the words

    for i in range( len(words[keys[1]])):
        w_Font.append(words[keys[1]][i])


    return w_Font


def drawWord(word, fsize):
    # returns an image of the given word in the given font size
    # the image is not cropped

    font = ImageFont.truetype("arial.ttf", fsize)
    w, h = font.getsize(word)

    im = Image.new('RGBA', (w,h), color = None)
    draw = ImageDraw.Draw(im)
    draw.text((0, 0), word, font = font)

    return im


def computeCanvasSize(words):
    #gets the dictionary of words (with keys: ['words', 'freq', 'size'])
    #returns the proposed (width, height) of the canvas

    W, H = 0, 0

    keys = list( words.keys() )

    for i in range(len(words[ keys[2] ])):
        fsize = words[keys[2]][i]
        font = ImageFont.truetype("arial.ttf", fsize)
        w, h = font.getsize(words[ keys[0]][i])

        W += w
        H += h

    return  int(0.5*W), H



def getBoxes_Nested(im, minW, minH):
    """
      returns the quad-tree of the image @im, i.e.
      a Tree, where the value of each node is a 4-tuple of ints (can be 2 for some of the leafs),
      representing min-max of hierarchic boxes
      here minW and minH are the width, height of the minimal box
    """

    box_0 = im.getbbox()  # the initial box

    p = Node(box_0, None) # the root of the tree
    T = Tree( p )

    stack = [ p ]  # (4 ints, a tuple)

    W, H = abs(box_0[0] - box_0[2]), abs(box_0[1] - box_0[3])

    if ( (H <= minH) and (W <= minW) ):
        # we do not split further if the height and width are small enough
        return T


    while stack:
        x = stack.pop()
        x_box = x.value    # the box coordinates
        full_node = True   # shows if the x is full

        W, H = abs(x_box[0] - x_box[2]), abs(x_box[1] - x_box[3])
        if ( (H <= minH) and (W <= minW)):
            continue

        #consider the 4 sub-boxes:

        if (x_box[0] + x_box[2])%2 == 0:
            d1 = (x_box[0] + x_box[2])>>1
        else:
            d1 = (x_box[0] + x_box[2] + 1)>>1

        if (x_box[1] + x_box[3])%2 == 0:
            d2 = (x_box[1] + x_box[3])>>1
        else:
            d2 = (x_box[1] + x_box[3] + 1)>>1

        # (x0, x1, d1, x3), (d1+1, x1, x2, d2), (x0, d2+1, d1, x3), (d1+1, d2+1, x2, x3)

        #we now set the children of x
        if ((H > minH) and (W > minW) ):
            #we need 4 sub-rectangles

            x_child = (x_box[0], x_box[1], d1, d2 )
            if im.crop(x_child).getbbox() is not None:
                x.child1 = Node( x_child, x )
                stack.append(x.child1)
            else:
                full_node = False

            x_child = (d1 , x_box[1], x_box[2], d2)
            if im.crop(x_child).getbbox() is not None:
                x.child2 = Node( x_child,  x )
                stack.append(x.child2)
            else:
                full_node = False

            x_child = (x_box[0], d2, d1, x_box[3])
            if im.crop(x_child).getbbox() is not None:
                x.child3 = Node( x_child,  x )
                stack.append(x.child3)
            else:
                full_node = False

            x_child = (d1 , d2 , x_box[2], x_box[3])
            if im.crop(x_child).getbbox() is not None:
                x.child4 = Node( x_child,  x )
                stack.append(x.child4)
            else:
                full_node = False

            x.isFull = full_node

        else:
            if (( H <= minH  ) and ( W > minW ) ): # don't split the y-coord, but only x

                x_child = (x_box[0], x_box[1], d1, x_box[3] )
                if im.crop(x_child).getbbox() is not None:
                    x.child1 = Node( x_child, x )
                    stack.append(x.child1)
                else:
                    full_node = False


                x_child = (d1, x_box[1], x_box[2], x_box[3] )
                if im.crop(x_child).getbbox() is not None:
                    x.child2 = Node( x_child, x )
                    stack.append(x.child2)
                else:
                    full_node = False

                x.isFull = full_node

            else: #we're in a position that we only split H

                x_child = (x_box[0], x_box[1], x_box[2], d2 )
                if im.crop(x_child).getbbox() is not None:
                    x.child1 = Node( x_child, x )
                    stack.append(x.child1)
                else:
                    full_node = False

                x_child = (x_box[0], d2, x_box[2], x_box[3] )
                if im.crop(x_child).getbbox() is not None:
                    x.child2 = Node( x_child, x )
                    stack.append(x.child2)
                else:
                    full_node = False


                x.isFull = full_node

    return T



def computeWordArea( T ):
    #given the quadtreee of a word, we compute the area occupied by the word's shape

    a = 0
    c = T.getLeafs()

    for r in c:
        a += rectArea(r.value)

    return a


def collision_test(T1, T2, shift1, shift2):
    """
       the input is a pair of trees representing the objects as a quad-tree
       shift_1 = (a1, b1) and shift2 = (a2, b2) are the left-top coordinats of the boxes on the large canvas
       this means that all boxes in T_i must be shifted by (a_i, b_i), where i = 1, 2

       return True iff the quad-trees have intersecting leaves, meaning the images they respresent actually intersect
    """

    r1, r2 = T1.root, T2.root

    if ( (not r1) or (not r2) ):
        return False


    stack = [ (r1, r2) ]

    while stack:
        p1, p2 = stack.pop()   # the nodes of the 1st and the 2nd trees

        if intersectionRect(p1.value, p2.value, shift1, shift2) == False:
            # if larger rectangles do not collide, their children will not collide either
            # hence no need to go for sub-nodes
            continue

        if ( p1.isLeaf() and p2.isLeaf() ):
            # leaves collide, we're done
            return True


        c1, c2 = p1.Children(), p2.Children()

        if not c1:
            for x in c2:
                stack.append( (p1, x) )
        else:
            if not c2:
                for x in c1:
                    stack.append( (x, p2) )
            else:
                # none are empty, i.e. the nodes are not leaves
                for x in c1:
                    for y in c2:
                        stack.append( (x, y) )


    return False


def insideCanvas( T, shift, canvas_size ):
    """
     @T is the tree-representation of a word, @shift is the word's bounding box's upper-left corner coord on canvas
     @canvas_size is a tuple (width, height) of the canvas

     returns True if the word's leaves stay inside the canvas
    """

    stack = [ T.root ]
    W, H = canvas_size
    sh_w, sh_h = shift


    while stack:
        v = stack.pop()

        a, b, c, d = v.value # a 4 tuple, left upper-coord and right-buttom coordinates
        if ( (a + sh_w < 0) or ( c + sh_w > W ) or (b + sh_h < 0) or (d + sh_h > H) ) == False:
            continue

        if v.isLeaf():
            return False

        stack += v.Children()

    return True


def copyTokens(tokens_with_freq, N_of_tokens_to_use):
    res = ''

    words = tokens_with_freq[0][0:N_of_tokens_to_use]
    sizes = tokens_with_freq[1][0:N_of_tokens_to_use]

    for i, word in enumerate(words):
        res += sizes[i]*(word + ' ')

    return res


def drawOnCanvas(tokens_with_freq,   placeInfo ):

    words = tokens_with_freq[0]
    sizes = tokens_with_freq[1]

    (c_W,c_H) = placeInfo[0]     # the suggested canvas size, might change here
    place = placeInfo[1]         # list of tuples, each for each word, showing the coordinate of the upper left corner
    word_img_size = placeInfo[2] # lisf of tuples, for each word, showing the size of the word's image

    word_img_path = placeInfo[3]

    #there might be some positions of words which fell out of the canvas
    # we first need to go through these exceptions, and expand the canvas and (or) shift the coordinate's origin.

    X_min, Y_min = 0, 0

    for i in range(len(place)):

        if place[i] is None:
            continue

        if X_min > place[i][0]:
            X_min = place[i][0]

        if Y_min > place[i][1]:
            Y_min = place[i][1]


    x_shift, y_shift = 0, 0
    if X_min < 0:
        x_shift = -X_min
    if Y_min < 0:
        y_shift = -Y_min

    X_max , Y_max = 0, 0
    for i in range( len(place) ):
        if place[i] is None:
            continue

        place[i] = ( place[i][0] + x_shift, place[i][1] + y_shift )
        if X_max < place[i][0] + word_img_size[i][0]:
            X_max = place[i][0] + word_img_size[i][0]
        if Y_max < place[i][1] + word_img_size[i][1]:
            Y_max = place[i][1] + word_img_size[i][1]

        word_img_path[i] = ( word_img_path[i][0] + x_shift, word_img_path[i][1] )


    if c_W < X_max:
        c_W = X_max
    if c_H < Y_max:
        c_H = Y_max

    im_canvas = Image.new('RGBA', (c_W + 10 ,c_H + 10 ), color = None )
    im_canvas_white = Image.new('RGBA', (c_W + 10 ,c_H + 10 ), color = (255,255,255,255) )

    dd = ImageDraw.Draw(im_canvas)
    dd_white = ImageDraw.Draw(im_canvas_white)

    color_schemes = [
        [ (89, 97, 113), (115, 124, 140), (141, 150, 168), (179, 188, 204), (219, 227, 240) ],
        [ (89, 97, 113), (115, 124, 140), (141, 150, 168) , (89, 97, 113), (89, 97, 113)],
        [ (120, 120, 120), (0,100,149),  (242, 99, 95), (0, 76, 112), (244,208,12) ],
        [ (14, 38, 50), (1,70,99),  (35, 118, 150), (180, 200, 207), (159,195,185) ],
        [ (3, 113, 146), (99,167,190),  (10, 31, 78), (252, 105, 53), (252,105,53) ],
        [ (12, 6, 54), (9,81,105),  (5, 155, 154), (83, 186, 131), (159,217,107) ] ,
        [ (100, 101, 165), (105,117,167),  (244, 233, 109), (242, 138, 49), (241,88,56) ],
        [ (171, 165, 191), (90,87,118),  (88, 62, 47), (241, 224, 214), (191,153,144) ],
        [ (25, 46, 91), (30,101,167),  (115, 162, 192), (0, 116, 63), (241,161,4) ]
    ]


    word_colors = color_schemes[ random.randint(0, len(color_schemes) - 1) ]

    max_size = max(sizes)

    for i in range( len(place) ):
        if place[i] is None:
            print('the word <' + words[i] + '> was skipped' )
        else:
            font1 = ImageFont.truetype("arial.ttf", sizes[i])

            if sizes[i] >= 0.7*max_size:
                c = word_colors[-1]
            elif ((sizes[i] >= 0.5*max_size)and(sizes[i]<0.7*max_size) ):
                c = word_colors[-2]
            elif ((sizes[i] >= 0.35*max_size)and(sizes[i]<0.5*max_size) ):
                c = word_colors[-3]
            elif ((sizes[i] >= 0.15*max_size)and(sizes[i]<0.35*max_size) ):
                c = word_colors[-4]
            else:
                c = word_colors[-5]


            dd.text( place[i], words[i], fill = c,  font = font1 )
            dd_white.text( place[i], words[i], fill = c,  font = font1 )


    enlarge_ = 5
    margin_size = 10

    box = im_canvas.getbbox()


    im_canvas_1 = Image.new('RGBA', ( box[2] - box[0] + 2*margin_size, box[3] - box[1] + 2*margin_size ), color = (100,100,100,100)  )
    im_canvas_1.paste( im_canvas_white.crop(box), ( margin_size, margin_size, margin_size + box[2] - box[0], margin_size + box[3] - box[1] ) )

    return im_canvas_1


def normalizeWordSize(tokens, N_of_tokens_to_use, max_size, min_size):

    words = tokens[0][0:N_of_tokens_to_use]
    sizes = tokens[1][0:N_of_tokens_to_use]

    sizes = [int(max_size*x/max(sizes)) for x in sizes]

    i = 0
    while i < len(sizes):
        if sizes[i] < min_size:
            del sizes[i]
            del words[i]
        else:
            i += 1

    return [words, sizes]



def placeWords(tokens_with_freq ):
    #gets a list of tokens and their frequencies
    #returns canvas size, locations of upper-left corner of words and words' sizes


    #1. we first create the QuadTrees for all words and determine a size for the canvas

    words = tokens_with_freq[0]
    sizes = tokens_with_freq[1]


    word_img_size = [] #list of tuples, collecting the drawn image sizes (width, height)

    word_img_path = [] #shows the path passed through the spiral before hitting a free space

    print('Number of words is ' + str(len(words)) + '\n')

    word_Trees = [] #list of trees
    H_W_quotient = [] #shows the quotient of Height/Width

    T_start = timeit.default_timer()

    c_W, c_H = 0, 0     #the proposed size of the canvas
    ensure_first = 2    #shows for how many words we need to reserve space on canvas


    total_area = 0
    avg_quotient = 0

    for i in range( len(words) ):

        im_tmp = drawWord(words[i], sizes[i] )
        T = getBoxes_Nested( im_tmp , 7, 7 )

        im_tmp = im_tmp.crop(im_tmp.getbbox())
        (a,b) = im_tmp.size
        H_W_quotient.append( b/a )


        T.compress() # we merge some leafs here, making the tree smaller
        word_Trees.append( T )

        word_img_size.append(im_tmp.size)

        if i < ensure_first:
            c_W += im_tmp.size[0]
            c_H += im_tmp.size[1]
        else:
            avg_quotient += H_W_quotient[i]
            total_area += computeWordArea( word_Trees[i] )


    if len(words)>ensure_first:
        avg_quotient = avg_quotient/( len(words) - ensure_first  )
    else:
        avg_quotient = 1


    T_stop = timeit.default_timer()


    #2. We now find places for the words on our canvas

    print('(i)  QuadTrees have been made for all words in ' + str( T_stop - T_start ) + ' seconds.\n')



    #c_W, c_H = 2000, 1200
    c_W, c_H = 3000, 1500


    print('(ii) Now trying to place the words.\n')

    T_start = timeit.default_timer()

    #3a. we start with the 1st word


    places = [ ]  #returned value; list of tuples representing places of words: if no suggested place, we put NONE
    ups_and_downs = [ random.randint(0,20)%2  for i in range(0, len(words) )]

    strLog = '' # the log file

    for i in range( len(words) ):

        print(  words[i], end = ', ' )

        strLog_word = '<' + words[i] + '>\n'

        a = 0.1 #the parameter of the spiral
        place_found = False

        if ups_and_downs[i] == 1:
            a = -a

        no_collision_place = [] #in case we don't get a place inside canvas, we collect legal (i.e. collision-free) places for further use

        #get some starting position on the canvas, in a strip near half of the width of canvas
        w, h = 0, 0
        if i == 0:
            w, h =  np.random.randint( int(0.3*c_W), int(0.5*c_W) ),   int(0.5*c_H) + np.random.randint( -50,50 )
        else:

            if sizes[i] < 0.3*max( sizes ):
                w, h =  np.random.randint( int(0.3*c_W), int(0.7*c_W) ),   int(0.5*c_H) + np.random.randint( -50,50 )
            else:
                w, h =  np.random.randint( int(0.3*c_W), int(0.7*c_W) ),   int(0.5*c_H) + np.random.randint( -50,50 )


        strLog_word += '   Starting position: (' + str(w) + ',' +str(h) + ')\n'

        if ups_and_downs[i] == 1:
            A = SP.Archimedian(a).generator
        else:
            A = SP.Rectangular(2, ups_and_downs[i]).generator

        dx0, dy0 = 0, 0

        place1 = (w,h)

        word_img_path.append( (w,h) )

        last_hit_index = 0 #we cache the index of last hit

        iter_ = 0

        start_countdown = False
        max_iter = 0

        for dx, dy in A:

            w, h = place1[0] + dx, place1[1] + dy


            if start_countdown == True:
                max_iter -= 1
                if max_iter == 0:
                    break
            else:
                iter_ += 1

            if ( (w<0)or(w>c_W)or(h<0)or(h>c_H) ): #fell outside the canvas area
                if start_countdown == False:
                    start_countdown = True
                    max_iter  = 1 + 10*iter_

                    strLog_word += '    Exited the canvas on step =' + str(iter_) + ' at (' + str(w) + ','  + str(h) +')\n'
                    strLog_word += '    Max_iter to complete =' + str(max_iter) +'\n'


            place1 = ( w, h )

            collision = False

            if last_hit_index < i:
                j = last_hit_index
                if places[j] is not None:
                    if collision_test(word_Trees[i], word_Trees[j], place1, places[j]) == True:
                        collision = True

            if collision == False:
                for j in range(0, i ): #check for collisions with the rest
                    if ((j != last_hit_index) and (places[j] is not None)):
                        if collision_test(word_Trees[i], word_Trees[j], place1, places[j]) == True:
                            collision = True
                            last_hit_index = j
                            break

            if collision == False:
                if insideCanvas( word_Trees[i] , place1, (c_W, c_H) ) == True:
                    places.append( place1 )
                    place_found = True
                    strLog_word += '    Place was found\n'
                    break # breaks the move in the Archimedian spiral
                else:
                    no_collision_place.append(  place1  )




        if place_found == False:

            print('no place was found')

            strLog_word += '    N of collision_free_outside canvas places =' + str(len(no_collision_place)) +'\n'

            if len(no_collision_place) == 0:
                places.append(None)
            else:
                if  i == 0 : # the first word
                    places.append( no_collision_place[0]  )
                else:
                    # print('BUT there is some outside the canvas')

                    #k1, k2 = int(0.5*c_W), int(0.5*c_H) #the centre of the canvas
                    k1, k2 =  int(0.5*(places[0][0] + word_img_size[0][0])), int(0.5*(places[0][1] + word_img_size[0][1]))

                    place1 = no_collision_place[0]
                    c_x, c_y = int(0.5*(place1[0] + word_img_size[i][0])),  int(0.5*(place1[1] + word_img_size[i][1]))
                    ds = (k1 - c_x)**2 + (k2 - c_y)**2
                    d_index = 0
                    for p in range(1, len(no_collision_place)):
                        place1 = no_collision_place[p]
                        c_x, c_y = int(0.5*(place1[0] + word_img_size[i][0])),  int(0.5*(place1[1] + word_img_size[i][1]))
                        ds_1 = (k1 - c_x)**2 + (k2 - c_y)**2
                        if ds_1<ds:
                            ds, d_index = ds_1 , p

                    places.append( no_collision_place[d_index] )
                    #NOTE!!! - - -  - - - TODO -  - - - - - -- -
                    #if the no collision place has negative (x or y), we need
                    #to to replace the origin of the canvas to accommodate those words



        strLog += strLog_word + '\n' + 'New size of the canvas = (' + str(c_W) +',' +  str(c_H)  +  ')\n\n'

    T_stop = timeit.default_timer()

    print('\n Words have been placed in ' + str( T_stop - T_start ) + ' seconds.\n')

    #with open('LogFile.txt', 'w+') as f:
    #    f.write(strLog)

    return [ (c_W, c_H),  places , word_img_size, word_img_path ]




def createWordle_fromFile( fName ):

    tokens = FR.tokenize_file_IntoWords(fName)
    tokens_with_freq = FR.tokenGroup(tokens)

    print('\n')

    for i in range(  min(10, len(tokens_with_freq) ) ):
        s = tokens_with_freq[1][i]
        print( str(s) +  (7-len(str(s)))*' ' + ':  ' + tokens_with_freq[0][i]  )


    N_of_words = 150
    tokens =  normalizeWordSize(tokens_with_freq, N_of_words, 250, 15)
    finalPlaces = placeWords(tokens)

    wordle = drawOnCanvas(tokens, finalPlaces)

    wordle.save( fName[0:-4] + '_wordle.png')

    print( 'the wordle image was sucessfully saved on the disc as <' + fName[0:-4]  + '_wordle.png >' )



if __name__ == "__main__":
    # waits for .txt fileName for processing
    createWordle_fromFile( sys.argv[1])
