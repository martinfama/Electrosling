def coor_to_pixel(coors = [0.0, 0.0], scale = 1.0, size = [0.0, 0.0], f_or_i = False):
    if not f_or_i:
        return [int(coors[0]*scale+size[0]/2), int(-coors[1]*scale+size[1]/2)]
    else:
        return [coors[0]*scale+size[0]/2.0, -coors[1]*scale+size[1]/2.0]
def pixel_to_coor(pixel = [0, 0]):
    return [int((pixel[0]-size[0]/2)/scale), int(-(pixel[1]+-size[0]/2)/scale)]
def in_box(dot = [0.0, 0.0], box = [0.0, 0.0, 0.0, 0.0]):
    if dot[0] > box[0] and dot[0] < box[0]+box[2] and dot[1] > box[1] and dot[1] < box[1]+box[3]:
        return True
    else:
        return False