import bpy

# Import relative modules
from .src import export_ui
from .src.config import get_config_at_startup


def register():
    export_ui.register()

    bpy.app.handlers.load_post.append(get_config_at_startup)


def unregister():
    export_ui.unregister()
