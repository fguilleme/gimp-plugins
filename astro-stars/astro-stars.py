#!/usr/bin/env python3
from struct import unpack
import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio
import time
import sys, os

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../')
from bsz_gimp_lib import PlugIn, ParamCombo, ParamString, ParamNumber, ParamBool

from sparkles import *

def save_image(image, drawable, file_path):
    interlace, compression = 0, 2
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
                Gio.File.new_for_path(file_path),
            ),
            GObject.Value(GObject.TYPE_BOOLEAN, interlace),
            GObject.Value(GObject.TYPE_INT, compression),

            GObject.Value(GObject.TYPE_BOOLEAN, True),
            GObject.Value(GObject.TYPE_BOOLEAN, True),
            GObject.Value(GObject.TYPE_BOOLEAN, False),
            GObject.Value(GObject.TYPE_BOOLEAN, True),
        ],
    )

def create_sparkles(image, drawable, name, fwhm, count, angle, size, max_opacity, th, sigma, acc):
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
                         type, 10,
                         Gimp.LayerMode.NORMAL)
        sparkles.fill(Gimp.FillType.TRANSPARENT)
        image.insert_layer(sparkles, None, 0)
    if not acc:
        sparkles.fill(Gimp.FillType.TRANSPARENT)

    Gimp.progress_pulse()
    # save layer as an image
    path = '/tmp/sparkles.png'
    save_image(image, tmp, path)

    stars = detect_stars(path, count=count, fwhm=fwhm, sigma=sigma, th=th)
    smallest = min([s[2] for s in stars])
    biggest = max([s[2] for s in stars])
    print(smallest, biggest)
    for x, y, flux in stars:
        Gimp.progress_pulse()
        rc=Gimp.context_set_brush('sparkle')
        if flux == smallest:
            bsize = 1
            opacity = 1
        else:
            ratio = (2*(flux-smallest) / (biggest-smallest))**2
            bsize = int(ratio*size/2)
            if bsize == 0:
                bsize = 1
            opacity = max(1, min(max_opacity, int(ratio * max_opacity)))
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

    # drawable.update(x, y, width, height)
    Gimp.displays_flush()

    Gimp.progress_end()
    image.undo_group_end()
    # Gimp.context_pop()

# create the plugin from bsz_gimp_lib
plugin = PlugIn(
    "Star sparkles",  # name
    create_sparkles,
    ParamString("Layer name", "sparkles"),
    ParamNumber("FWMH", 7, 1, 30, ui_step=0.5),
    ParamNumber("Count", 500, 10, 2000, ui_step=10),
    ParamNumber("Angle", 35, 0, 180, ui_step=5),
    ParamNumber("Size", 50, 10, 1000, ui_step=5),
    ParamNumber("Max opacity", 20, 10, 100, ui_step=1),
    ParamNumber("Threshold", 1, 1, 15, ui_step=1),
    ParamNumber("Sigma", 2, 1, 5, ui_step=1),
    ParamBool("Accumulative", True),
    description="Add star sparkles",
    images="RGB*, GRAY*",
    path = "<Image>/Astro/",
    authors = "François Guillemé",
    date = "2022"
)

Gimp.main(plugin.Procedure.__gtype__, sys.argv)
