import bpy


class glTFGodotScene(bpy.types.PropertyGroup):
    object_name: bpy.props.StringProperty()
    scene_path: bpy.props.StringProperty()
