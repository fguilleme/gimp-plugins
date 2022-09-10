#!/usr/bin/env python3
from struct import unpack
import math
import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GObject
from gi.repository import Gio
import sys, os

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
from bsz_gimp_lib import PlugIn, ParamString, ParamNumber

from sparkles import *

@timeit
def save_image(image, drawable, path):
    Gimp.get_pdb().run_procedure(
        "file-png-save",
        [
            GObject.Value(Gimp.RunMode, Gimp.RunMode.NONINTERACTIVE),
            GObject.Value(Gimp.Image, image),
            GObject.Value(GObject.TYPE_INT, 1),
            GObject.Value(
                Gimp.ObjectArray, Gimp.ObjectArray.new(Gimp.Drawable, [drawable], 0)
            ),
            GObject.Value(
                Gio.File,
                Gio.File.new_for_path(path),
            ),
            GObject.Value(GObject.TYPE_BOOLEAN, False),
            GObject.Value(GObject.TYPE_INT, False),

            GObject.Value(GObject.TYPE_BOOLEAN, True),
            GObject.Value(GObject.TYPE_BOOLEAN, True),
            GObject.Value(GObject.TYPE_BOOLEAN, False),
            GObject.Value(GObject.TYPE_BOOLEAN, True),
        ],
    )

@timeit
def create_sparkles(image, _, name, count, size1, size2, angle):
    # Gimp.context_push()
    image.undo_group_start()
    Gimp.progress_init('Detect stars...')

    if image.get_base_type() is Gimp.ImageBaseType.RGB:
        type = Gimp.ImageType.RGBA_IMAGE
    else:
        type = Gimp.ImageType.GRAYA_IMAGE
    tmp = Gimp.Layer.new_from_visible(image, image, name)

    sparkles = image.get_layer_by_name(name)
    if sparkles is None:
        sparkles = Gimp.Layer.new(image, name,
                         tmp.get_width(), tmp.get_height(),
                         type, 20,
                         Gimp.LayerMode.NORMAL)
        sparkles.fill(Gimp.FillType.TRANSPARENT)
        image.insert_layer(sparkles, None, 0)
    sparkles.fill(Gimp.FillType.TRANSPARENT)

    Gimp.progress_pulse()
    # save layer as an image
    path = '/tmp/sparkles.png'
    save_image(image, tmp, path)

    stars = detect_stars(path, count=count)
    ff = [f for x, y, f in stars]
    mx = max(ff)
    for x, y, flux in stars:
        flux = math.sqrt((flux/mx))
        Gimp.progress_pulse()
        bsize =  size1 + (size2 - size1)  * flux
        opacity = min(100, max(5, round(100*flux)))
        # Gimp.context_set_brush('sparkle')
        Gimp.context_set_brush_size(bsize)
        Gimp.context_set_opacity(opacity)
        Gimp.context_set_paint_mode(Gimp.LayerMode.NORMAL)
        Gimp.context_set_brush_angle(angle)
        Gimp.context_set_background(Gimp.RGB())
        try:
            rgb = unpack('4f', tmp.get_pixel(int(x) , int(y)))
        except:
            # PNG files
            rgb = [1,1,1,1]

        _color = Gimp.RGB()
        _color.set(rgb[0], rgb[1], rgb[2])
        Gimp.context_set_foreground(_color)
        Gimp.paintbrush_default(sparkles, [x, y])

    Gimp.displays_flush()

    Gimp.progress_end()
    image.undo_group_end()
    # Gimp.context_pop()

# create the plugin from bsz_gimp_lib
plugin = PlugIn(
    "Star sparkles",  # name
    create_sparkles,
    ParamString("Layer name", "sparkles"),
    ParamNumber("Count", 500, 10, 2000, ui_step=10),
    ParamNumber("Minimum Size", 50, 50, 200, ui_step=10),
    ParamNumber("Maximum Size", 200, 50, 1000, ui_step=50),
    ParamNumber("Angle", 35, 0, 180, ui_step=5),
    description="Add star sparkles",
    images="RGB*, GRAY*",
    path = "<Image>/Astro/",
    authors = "François Guillemé",
    date = "2022"
)

Gimp.main(plugin.Procedure.__gtype__, sys.argv)
