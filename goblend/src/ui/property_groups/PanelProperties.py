import bpy

from .enum_items import transparency_enum_items, culling_enum_items

hierarchy_defaults = [
    ("DEFAULT", "Default", "Use the default value from the config file"),
    ("YES", "Yes", "Use the same folder hierarchy in Godot to save"),
    ("NO", "No", "Put the result directly into the save directory, do not use the same hierarchy"),
]

collision_defaults = [
    ("DEFAULT", "Default", "Use the default value from the config file"),
    ("YES", "Yes", "Reuse collision shapes"),
    ("NO", "No", "Do not reuse collision shapes"),
]


class PanelProperties(bpy.types.PropertyGroup):
    open_paths_panel: bpy.props.BoolProperty(default=True)
    same_hierarchy_target: bpy.props.StringProperty(
        name="Same Hierarchy Target",
        description="The root directory to use to build the final path when using one of the 'use same hierarchy' settings. See documentation for more info.",
        subtype="FILE_PATH",
        default="Default",
    )
    scene_save_path: bpy.props.StringProperty(
        name="Scene Save Path",
        description="The path to save the Godot scene at",
        subtype="FILE_PATH",
        default="Default",
    )
    scene_use_same_hierarchy: bpy.props.EnumProperty(
        name="Scene Use Same Hierarchy",
        description="Whether to save the resulting scene using the same folder hierarchy at the save path as the hierarchy for this blend file",
        items=hierarchy_defaults,
        default="DEFAULT",
    )
    material_save_path: bpy.props.StringProperty(
        name="Material Save Path",
        description="The path to save Godot materials at",
        subtype="FILE_PATH",
        default="Default",
    )
    material_use_same_hierarchy: bpy.props.EnumProperty(
        name="Material Use Same Hierarchy",
        description="Whether to save the resulting materials using the same folder hierarchy at the save path as the hierarchy for this blend file",
        items=hierarchy_defaults,
        default="DEFAULT",
    )
    texture_save_path: bpy.props.StringProperty(
        name="Texture Save Path",
        description="The path to save the generated textures at",
        subtype="FILE_PATH",
        default="Default",
    )
    texture_use_same_hierarchy: bpy.props.EnumProperty(
        name="Texture Use Same Hierarchy",
        description="Whether to save the resulting textures using the same folder hierarchy at the save path as the hierarchy for this blend file",
        items=hierarchy_defaults,
        default="DEFAULT",
    )
    animation_library_save_path: bpy.props.StringProperty(
        name="Animation Library Save Path",
        description="The path to save the generated animation library at",
        subtype="FILE_PATH",
        default="Default",
    )
    animation_library_use_same_hierarchy: bpy.props.EnumProperty(
        name="Animation Library Use Same Hierarchy",
        description="Whether to save the resulting animation library using the same folder hierarchy at the save path as the hierarchy for this blend file",
        items=hierarchy_defaults,
        default="DEFAULT",
    )
    animation_save_path: bpy.props.StringProperty(
        name="Animation Save Path",
        description="The path to save the generated animations at",
        subtype="FILE_PATH",
        default="Default",
    )
    animation_use_same_hierarchy: bpy.props.EnumProperty(
        name="Animation Use Same Hierarchy",
        description="Whether to save the resulting animations using the same folder hierarchy at the save path as the hierarchy for this blend file",
        items=hierarchy_defaults,
        default="DEFAULT",
    )
    shader_save_path: bpy.props.StringProperty(
        name="Shader Save Path",
        description="The path to save the generated shaders at",
        subtype="FILE_PATH",
        default="Default",
    )
    shader_use_same_hierarchy: bpy.props.EnumProperty(
        name="Shader Use Same Hierarchy",
        description="Whether to save the resulting shaders using the same folder hierarchy at the save path as the hierarchy for this blend file",
        items=hierarchy_defaults,
        default="DEFAULT",
    )
    collision_shapes_save_path: bpy.props.StringProperty(
        name="Collision Shape Save Path",
        description="The path to save the generated collision shapes at",
        subtype="FILE_PATH",
        default="Default",
    )
    reuse_collision_shapes: bpy.props.EnumProperty(
        name="Reuse Collision Shapes",
        description="Whether to save the generated collision shapes separately so that they can be reused across scenes",
        items=collision_defaults,
        default="DEFAULT",
    )

    texture_dim: bpy.props.IntVectorProperty(
        name="Dimensions",
        description="Dimensions of the generated texture",
        size=2,
        subtype="COORDINATES",
        default=(1024, 1024),
        min=0,
    )
    transparency_mode: bpy.props.EnumProperty(
        name="Transparency Mode",
        description="Only affects transparent objects! Transparency mode to use in Godot",
        items=transparency_enum_items,
        default="DEPTH_PRE_PASS",
    )
    transparency_alpha_scissor_threshold: bpy.props.FloatProperty(
        name="Scissor Threshold", min=0.0, max=1.0, precision=3, default=0.5
    )

    cull_mode: bpy.props.EnumProperty(
        name="Cull Mode",
        description="The cull mode to use for objects in Godot",
        items=culling_enum_items,
        default="BACK",
    )
