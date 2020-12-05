def fn1(iters):
    s = ''
    a = 1
    while iters > 0:
        s += f'{a*a}'
        a += 1
    return s


def fn2(ct):
    s = ''
    a = 1
    if ct > 0:
        while ct > 0:
            s += f'{a*a}'
            a += 1
    return s