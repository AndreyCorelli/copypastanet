import math


def func_a(x: int, pref: str):
    y = math.sin(x/180*3.14)
    if y < 0:
        y = -y
    print('{0}: sin{1} = {2}'.format(pref, x, y))


def func_b(z: int, pref: str):
    y = math.sin(z / 180 * 3.14)
    if y < 0 :
        y = -y

    print('{0}: sin{1} = {2}'.format(pref, z, y))
