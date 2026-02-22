import bpy

bl_info = {
    "name": "Goblend: Export to Godot",
    "description": "Export complex scenes to Godot with this customizable addon!",
    "author": "https://github.com/Togira123",
	"version": (1, 0, 0),
    "blender": (4, 5, 5),
    "location": "Properties &gt; Scene & gt; Export to Godot",
    "category": "Game Engine",
}

# Import relative modules
from .src import export_ui
from .src.config import get_config_at_startup

def register():
    export_ui.register()

    bpy.app.handlers.load_post.append(get_config_at_startup)

def unregister():
    export_ui.unregister()
