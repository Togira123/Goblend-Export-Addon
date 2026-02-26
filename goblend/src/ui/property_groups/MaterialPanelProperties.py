import bpy

from .enum_items import transparency_enum_items, culling_enum_items

def can_add_material(self, material):
    scene = bpy.context.scene
    if material.library != None:
        return False
    for mat_setting in scene.material_panel_props:
        if mat_setting.mat == material:
            return False
    return True

class MaterialPanelProperties(bpy.types.PropertyGroup):
    open: bpy.props.BoolProperty(default=True)
    mat: bpy.props.PointerProperty(
        name="Material",
        type=bpy.types.Material,
        poll=can_add_material
    )

    force_texture_group_disabled: bpy.props.StringProperty(
        name="Texture Group",
        description="Texture group cannot be used together with the 'Use Godot Shader' option",
        default=""
    )

    texture_group: bpy.props.StringProperty(
        name="Texture Group",
        description="Materials with the same texture group will bake textures to the same image file. Not compatible with 'Use Godot Shader'",
        default=""
    )
    
    use_shader: bpy.props.BoolProperty(
        name="Use Godot Shader",
        description="Attempt to convert this material into a Godot Shader. Only a small subset of nodes is supported, check the documentation to see which.",
        default=False
    )

    override_texture_size: bpy.props.BoolProperty(
        name="Override Texture Size",
        description="Override texture size for this material",
        default=False
    )

    texture_dim: bpy.props.IntVectorProperty(
        name="Dimensions Override",
        description="Dimensions of the generated texture",
        size=2,
        subtype="COORDINATES",
        default=(1024, 1024),
        min=0
    )

    force_override_bake_margin_disabled: bpy.props.BoolProperty(
        name="Override Bake Margin",
        description="Bake margin cannot be used together with the 'Use Godot Shader' option",
        default=False 
    )
    
    override_bake_margin: bpy.props.BoolProperty(
        name="Override Bake Margin",
        description="Change the bake margin used when baking this material to textures. Not compatible with 'Use Godot Shader'",
        default=False
    )

    bake_margin: bpy.props.IntProperty(
        name="Bake Margin",
        description="The bake margin to use when baking this material",
        min=0,
        default=4
    )
    
    transparency_mode: bpy.props.EnumProperty(
        name="Transparency Mode",
        description="Only affects transparent objects! Transparency mode to use in Godot for this material",
        items=[("DEFAULT", "Default", "Use the default specified at the top global settings")] + transparency_enum_items,
        default="DEFAULT"
    )
    transparency_alpha_scissor_threshold: bpy.props.FloatProperty(
        name="Scissor Threshold",
        min=0.0,
        max=1.0,
        precision=3,
        default=0.5
    )
    
    cull_mode: bpy.props.EnumProperty(
        name="Cull Mode",
        description="The cull mode to use for this material in Godot",
        items=[("DEFAULT", "Default", "Use the default specified at the top global settings")] + culling_enum_items,
        default="DEFAULT"
    )

    limit_uv_effect_normal: bpy.props.BoolProperty(
        name="Limit Normal UV Effect",
        description="Define boundaries in which the normal map is applied",
        default=False
    )
    limit_uv_effect_normal_x_min: bpy.props.FloatProperty(
        name="X Min",
        min=0.0,
        max=1.0,
        precision=6,
        default=0.0
    )
    limit_uv_effect_normal_x_max: bpy.props.FloatProperty(
        name="X Max",
        min=0.0,
        max=1.0,
        precision=6,
        default=1.0
    )
    limit_uv_effect_normal_y_min: bpy.props.FloatProperty(
        name="Y Min",
        min=0.0,
        max=1.0,
        precision=6,
        default=0.0
    )
    limit_uv_effect_normal_y_max: bpy.props.FloatProperty(
        name="Y Max",
        min=0.0,
        max=1.0,
        precision=6,
        default=1.0
    )
