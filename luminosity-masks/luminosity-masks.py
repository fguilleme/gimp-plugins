#!/usr/bin/env python3
import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio
import sys

def N_(message): return message
def _(message): return GLib.dgettext(None, message)

def create_luminosity_masks(procedure, run_mode, image, n_drawables, drawables, args, data):
    Gimp.context_push()

    _color = Gimp.RGB()
    _color.set(0, 0, 0)
    
    image.undo_group_start()
    d = drawables[0]
    LMask =  Gimp.Layer.new_from_drawable(d, image)
    width = d.get_width()
    height = d.get_height()
    LMask.set_name('Light')
    image.insert_layer(LMask, d.get_parent(), image.get_item_position(d))
    LMask.desaturate(3)

    L = Gimp.Channel.new(image, 'L',  width, height, 100, _color)
    image.insert_channel(L, None, 0)
    L.set_visible(False)
    Gimp.edit_copy([LMask])
    Gimp.floating_sel_anchor(Gimp.edit_paste(L, True)[0])
    image.select_item(2, LMask)

    # Subtract the "L" channel from the image (giving us "D")
    image.select_item(1, L)
    Gimp.Selection.save(image).set_name('D')
    #
    # ; Subtract again, DD
    image.select_item(1, L)
    Gimp.Selection.save(image).set_name('DD')
    #
    # ; Subtract again, DDD
    image.select_item(1, L)
    Gimp.Selection.save(image).set_name('DDD')
    #
    D = image.get_channel_by_name('D')
    DD = image.get_channel_by_name('DD')
    DDD = image.get_channel_by_name('DDD')
    #
    # ; Activate "L" again
    image.select_item(2, L)
    #
    # ; Subtract "D" from "L", giving us "LL"
    image.select_item(1, D)
    Gimp.Selection.save(image).set_name('LL')
    #
    # ; Subtract "D" from "LL", giving us "LLL"
    image.select_item(1, D)
    Gimp.Selection.save(image).set_name('LLL')
    #
    LL = image.get_channel_by_name('LL')
    LLL = image.get_channel_by_name('LLL')
    #
    # ; Now build the mid tone masks
    image.select_item(2, L)
    #
    # ; And intersect the "D" mask, saving new selection as "M"
    image.select_item(3, D)
    Gimp.Selection.save(image).set_name('M')
    #
    # ; Select the entire image
    image.select_item(2, LMask)
    #
    image.select_item(1, LL)
    image.select_item(1, DD)
    Gimp.Selection.save(image).set_name('MM')
    #
    # ; Select the entire image
    image.select_item(2, LMask)
    #
    # ;Subtract "DDD" and "LLL" to get "MMM"
    image.select_item(1, LLL)
    image.select_item(1, DDD)
    Gimp.Selection.save(image).set_name('MMM')
    #
    # ; Remove temp desat layer
    image.remove_layer(LMask)
    #
    # ; De-Select Everything
    Gimp.Selection.none(image)
    #
    # ; Re-activate original layer
    image.set_active_layer(d)

    image.undo_group_end()
    
    Gimp.context_pop()
    return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

class luminosity_masks (Gimp.PlugIn):
    ## Parameters ##
    __gproperties__ = {
    }
    ## GimpPlugIn virtual methods ##
    def do_set_i18n(self, procname):
        return True, 'gimp30-python', None

    def do_query_procedures(self):
        return [ 'create-luminosity-masks' ]

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name,
                                            Gimp.PDBProcType.PLUGIN,
                                           create_luminosity_masks, None)
        procedure.set_image_types("RGB*, GRAY*");
        procedure.set_sensitivity_mask (Gimp.ProcedureSensitivityMask.DRAWABLE |
                                        Gimp.ProcedureSensitivityMask.DRAWABLES)
        procedure.set_menu_label(_("_Luminosity masks"))
        procedure.set_attribution("F. Guillemé",
                                  "F. Guillemé",
                                  "2022")
        procedure.add_menu_path ("<Image>/Filters/Generic")
        return procedure

Gimp.main(luminosity_masks.__gtype__, sys.argv)

