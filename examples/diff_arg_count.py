import math


def func_a(x: int, pref: str):
    y = math.sin(x/180*3.14)
    if y < 0:
        y = -y
    print('{0}: sin{1} = {2}'.format(pref, x, y))


def func_b(a: str, z: int, pref: str):
    d = math.sin(z / 180 * 3.14)
    if d < 0:
        d = -d

    print('{0}: sin{1} = {2}'.format(pref, z, d))
    a = a + ' ' + str(d if d > 0 else z)
    print(a)
