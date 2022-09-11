import sys
import os
from time import time

# hack to grab PYTHONPATH from .config/GIMP/2.99/environ/python.env
if 'PYTHONPATH' in os.environ:
    sys.path.insert(0, os.environ['PYTHONPATH'])

import numpy as np
from PIL import Image
import sep

def timeit(func):
    # This function shows the execution time of 
    # the function object passed
    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        print(f'Function {func.__name__!r} executed in {(t2-t1):.4f}s')
        return result
    return wrap_func

@timeit
def detect_stars(path, count):
    image = Image.open(path).convert('L').point( lambda p: 255 if p > 100 else 0 )
    data = np.asarray(image).copy().astype(np.float64)

    # m, s = np.mean(data), np.std(data)
    bkg = sep.Background(data)
    data_sub = data - bkg
    objects = sep.extract(data_sub, 1.5, err=bkg.globalrms)

    # res = [[int(o['x']), int(o['y']), round(math.sqrt(o['flux']),2)] for o in objects if o['flux'] > 100]
    res = [[int(o['x']), int(o['y']), round(o['npix'],2)] for o in objects]
    res = sorted(res, key=lambda a: a[2], reverse=True)
    while len(res) > 1 and res[0][2] > res[1][2]*2:
        res = res[1:]

    res = res[:int(count)]
    return [[x,y,n] for x,y,n in res]

if __name__ == '__main__':
    print(detect_stars(*sys.argv[1:]))

