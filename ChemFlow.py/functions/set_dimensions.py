def set_dimensions(arguments) :
    '''
    Set necessary dimensions
    '''
    
    # NOTE: if "blind" is active, dimensions must be recalculated on the fly

    if arguments['software'] in ['vina','qvina','smina'] and not arguments['size'] :
            print('[ Error ] --size was not specified')
            quit()

    if arguments['software'] in ['plants'] :
        # Specific arguments for PLANTS/GOLD
        radius     = arguments['radius']
        if not radius :
            print('DockFlow.py: error: the following arguments are required: --radius')
            quit()
    else : 
        radius = None

    return (size, radius)


def max_distance(points_axis, center_axis):
    dmax = 0
    for p in points_axis:
        d = abs(p - center_axis)
        if d > dmax:
            dmax = d
    return dmax

def binding_box(ref_ligand,padding):
    with open(ref_ligand,'r') as molecule :
        read_coordinates = False
        for line in molecule :
            if line.startswith('@<TRIPOS>BOND') :
                break
            if read_coordinates :
                c = line.split()
                x.append(float(c[2]))
                y.append(float(c[3]))
                z.append(float(c[4]))
                continue
            if line.startswith('@<TRIPOS>ATOM') :
                read_coordinates = True
                x = []
                y = []
                z = []

    if read_coordinates :
        n = len(x)
        cx=sum(x)/n
        cy=sum(y)/n
        cz=sum(z)/n
        if padding is None:
            padding = 0
        sx = (max_distance(x, cx) + padding)*2
        sy = (max_distance(y, cy) + padding)*2
        sz = (max_distance(z, cz) + padding)*2
        return cx, cy, cz, sx, sy, sz
    else :
        print("Could not read coordinates!")
        quit()
