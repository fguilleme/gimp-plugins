#!/usr/bin/env python3
#   Copyright (C) 1997  James Henstridge <james@daa.com.au>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
import sys
from sparkles import *

def N_(message): return message
def _(message): return GLib.dgettext(None, message)

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

def create_sparkles(procedure, run_mode, image, n_drawables, drawables, args, data):
    config = procedure.create_config()
    config.begin_run(image, run_mode, args)

    if run_mode == Gimp.RunMode.INTERACTIVE:
        GimpUi.init('astro-star-sparkles')
        dialog = GimpUi.ProcedureDialog(procedure=procedure, config=config)
        dialog.fill(None)
        if not dialog.run():
            dialog.destroy()
            config.end_run(Gimp.PDBStatusType.CANCEL)
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        else:
            dialog.destroy()

    # color      = config.get_property('color')
    name  = config.get_property('name')
    fwhm  = config.get_property('fwhm')
    count = config.get_property('count')
    angle = config.get_property('angle')

    Gimp.context_push()
    image.undo_group_start()
    Gimp.progress_init('Detect stars...')

    if image.get_base_type() is Gimp.ImageBaseType.RGB:
        type = Gimp.ImageType.RGBA_IMAGE
    else:
        type = Gimp.ImageType.GRAYA_IMAGE
    for drawable in drawables:
        tmp = Gimp.Layer.new_from_visible(image, image, name)

        sparkles = Gimp.Layer.new(image, name,
                             tmp.get_width(), tmp.get_height(),
                             type, 20,
                             Gimp.LayerMode.NORMAL)
        sparkles.fill(Gimp.FillType.TRANSPARENT)
        image.insert_layer(sparkles, drawable.get_parent(),
                           image.get_item_position(drawable))

        Gimp.progress_pulse()
        # save layer as an image
        path = '/tmp/sparkles.png'
        save_image(image, tmp, path)

        stars = detect_stars(path, count=count, fwhm=fwhm)
        biggest = max([s[2] for s in stars])
        for x,y,flux in stars:
            Gimp.progress_pulse()
            # Gimp.context_set_brush('sparkle')
            size = flux/biggest
            Gimp.context_set_brush_size(200*size)
            Gimp.context_set_opacity(size*100)
            Gimp.context_set_paint_mode(Gimp.LayerMode.NORMAL)
            Gimp.context_set_brush_angle(angle)
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
    Gimp.context_pop()

    config.end_run(Gimp.PDBStatusType.SUCCESS)

    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

_color = Gimp.RGB()
_color.set(240.0, 0, 0)

class Sparkles (Gimp.PlugIn):
    ## Parameters ##
    __gproperties__ = {
        "name": (str,
                 _("Layer _name"),
                 _("Layer name"),
                 _("Sparkles"),
                 GObject.ParamFlags.READWRITE),
        "fwhm": (float,
                       _("FWHM"),
                       _("fwhm"),
                       1.0, 7.0, 2.0,
                       GObject.ParamFlags.READWRITE),
        "count": (int,
                    _("Count"),
                    _("count"),
                    1, 100, 10,
                    GObject.ParamFlags.READWRITE),
        "angle": (int,
                    _("Angle"),
                    _("angle"),
                    1, 360, 10,
                    GObject.ParamFlags.READWRITE),
    }
    ## GimpPlugIn virtual methods ##
    def do_set_i18n(self, procname):
        return True, 'gimp30-python', None

    def do_query_procedures(self):
        return [ 'astro-star-sparkles' ]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name,
                                            Gimp.PDBProcType.PLUGIN,
                                           create_sparkles, None)
        procedure.set_image_types("RGB*, GRAY*");
        procedure.set_sensitivity_mask (Gimp.ProcedureSensitivityMask.DRAWABLE |
                                        Gimp.ProcedureSensitivityMask.DRAWABLES)
        procedure.set_documentation (_("Add a layer of star sparkles"),
                                     _("Adds a layer of star sparkles"),
                                     name)
        procedure.set_menu_label(_("_Star sparkles"))
        procedure.set_attribution("F. Guillemé",
                                  "F. Guillemé",
                                  "2022")
        procedure.add_menu_path ("<Image>/Astro")

        procedure.add_argument_from_property(self, "name")
        procedure.add_argument_from_property(self, "fwhm")
        procedure.add_argument_from_property(self, "count")
        procedure.add_argument_from_property(self, "angle")
        return procedure

Gimp.main(Sparkles.__gtype__, sys.argv)
