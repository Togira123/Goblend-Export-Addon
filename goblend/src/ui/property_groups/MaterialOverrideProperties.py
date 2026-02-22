import bpy

from .enum_items import transparency_enum_items, culling_enum_items

def can_add_material(self, material):
    scene = bpy.context.scene
    obj_mats = set()
    for slot in self.obj.material_slots:
        obj_mats.add(slot.material)
    panel = None
    for item in scene.object_constraints_panel_props:
        if item.obj == self.obj:
            panel = item
            break
    if panel == None:
        return False
    
    for override in panel.material_overrides:
        obj_mats.discard(override.mat)
    return material in obj_mats

class MaterialOverrideProperties(bpy.types.PropertyGroup):
    open: bpy.props.BoolProperty(default=True)
    obj: bpy.props.PointerProperty(
        name="Object",
        type=bpy.types.Object,
    )
    mat: bpy.props.PointerProperty(
        name="Material",
        type=bpy.types.Material,
        poll=can_add_material
    )
    
    use_shader: bpy.props.BoolProperty(
        name="Use Godot Shader",
        description="Attempt to convert this material into a Godot Shader. Only a small subset of nodes is supported, check the documentation to see which.",
        default=False
    )

    override_quality: bpy.props.BoolProperty(
        name="Override Texture Quality",
        description="Override texture quality by adjusting the texture size",
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

    uv_map_enabled: bpy.props.BoolProperty(
        name="Override UV Map",
        description="Whether to use a separate UV Map as bake target",
        default=False
    )

    force_uv_map_disabled: bpy.props.BoolProperty(
        name="Override UV Map",
        description="Disabled: Incompatible with the 'Use Shader' Setting. Set the UV Map on the Shader itself instead, or disable 'Use Shader'.",
        default=False
    )
    
    uv_map_per_texture_enabled: bpy.props.BoolProperty(
        name="Per Texture",
        description="Whether to use a different UV map per texture",
        default=False
    )
    
    def uvmaps(self, context):
        if self.obj:
            return [(uv.name, uv.name, "") for uv in self.obj.data.uv_layers][:8]  # godot only allows up to 8 uv maps
        return []
    
    uv_map: bpy.props.EnumProperty(
        name="UV Map",
        items=uvmaps
    )
    uv_map_base_color: bpy.props.EnumProperty(
        name="Base Color",
        items=uvmaps
    )
    uv_map_metallic_roughness: bpy.props.EnumProperty(
        name="Metallic/Roughness",
        items=uvmaps
    )
    uv_map_normal: bpy.props.EnumProperty(
        name="Normal",
        items=uvmaps
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
