GIMP 2.99 python plugin to add a layer for star sparkles.

It requires numpy, PIL, astropy and  phoutils python modules to be installed

Basically it detects stars in a current images draw on stroke withe current brush with the size
and opacity relative the star flux.

It also get the color of the pixel at the star location for the brush

But before you need to create the sparkles brush. It can be done easily with a diamond brush with 4 spikes and a big aspect ratio and hardness to a small value.


*BEFORE*
![After](https://github.com/fguilleme/astro-stars/blob/42bd043e84951b138a66b5698aecf0c694ddddc0/original.jpg)

*AFTER*
![After](https://github.com/fguilleme/astro-stars/blob/42bd043e84951b138a66b5698aecf0c694ddddc0/star-sparkles.jpg)
