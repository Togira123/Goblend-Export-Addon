import bpy


class glTFSavePaths(bpy.types.PropertyGroup):
    scene_save_path: bpy.props.StringProperty()
    material_save_path: bpy.props.StringProperty()
    texture_save_path: bpy.props.StringProperty()
    animation_library_save_path: bpy.props.StringProperty()
    animation_save_path: bpy.props.StringProperty()
    shader_save_path: bpy.props.StringProperty()
    collision_shapes_save_path: bpy.props.StringProperty()

    @classmethod
    def paths(cls):
        return list(cls.__annotations__.keys())
