import bpy

from .src import export_ui
from .src.config import get_config_at_startup

# this import is needed for the glTF extension to register
from .src.export.glTF2ExportUserExtension import glTF2ExportUserExtension


def register():
    export_ui.register()
    bpy.app.handlers.load_post.append(get_config_at_startup)


def unregister():
    export_ui.unregister()
    bpy.app.handlers.load_post.remove(get_config_at_startup)
