import sys
import os

# hack to grab PYTHONPATH from .config/GIMP/2.99/environ/python.env
if 'PYTHONPATH' in os.environ:
    sys.path.insert(0, os.environ['PYTHONPATH'])

import numpy as np
from PIL import Image

from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
from photutils.detection import find_peaks

def detect_stars(path, count=20, fwhm=3.0, th=5.0, sigma=3):
    image = Image.open(path).convert('L')
    data = np.asarray(image)

    mean, median, std = sigma_clipped_stats(data, sigma=sigma)
    daofind = DAOStarFinder(fwhm=fwhm, threshold=th*std, brightest=count)
    sources = daofind(data - median)
    positions = np.transpose((sources['xcentroid'], sources['ycentroid'], sources['flux']))
    return positions

if __name__ == '__main__':
    print(detect_stars(sys.argv[1], 20))

