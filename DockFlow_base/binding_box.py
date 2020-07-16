#!/usr/bin/env python3
# coding: utf-8
# Config

def max_distance(points_axis, center_axis):
    dmax = 0
    for p in points_axis:
        d = abs(p - center_axis)
        if d > dmax:
            dmax = d
    return dmax

def binding_box(ligand, padding):
    with open(ligand,'r') as molecule :
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
        sx = (max_distance(x, cx) + padding)*2
        sy = (max_distance(y, cy) + padding)*2
        sz = (max_distance(z, cz) + padding)*2
        # sx = abs(max(x)-min(x)) + padding
        # sy = abs(max(y)-min(y)) + padding
        # sz = abs(max(z)-min(z)) + padding
        print(f'--center_x {cx:.3f} --center_y {cy:.3f} --center_z {cz:.3f} --size_x {sx:.3f} --size_y {sy:.3f} --size_z {sz:.3f}')
    else :
        print("Could not read coordinates!")
def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Reads a mol2 file and returns the center and size of the smallest shape containing all the atoms of the given molecule.")
    parser.add_argument('ligand',
                        metavar  ='MOL2 FILE',
                        help     ='Automaticaly calculate center_x, center_y, center_z, '\
                                   'size_x, size_y and size_z for vina based on the ligand. It uses '\
                                   'the argument provided (mol2) as reference ligand.')
    parser.add_argument('--padding',
                        dest    ='padding',
                        type    =float,
                        default =0.0,
                        metavar ='FLOAT',
                        required=False,
                        help    ='Extra space for the binding box')
    arg_dict = vars(parser.parse_args())
    binding_box(arg_dict['ligand'], arg_dict['padding'])

if __name__=='__main__': main()
