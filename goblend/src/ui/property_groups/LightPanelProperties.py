import bpy

from math import radians

from .MaterialOverrideProperties import MaterialOverrideProperties

from .enum_items import shadow_cast_enum_items

def can_add_light(self, obj):
    if obj.type != "LIGHT":
        return False
    light = obj.data
    if light is bpy.types.AreaLight:
        return False
    for item in bpy.context.scene.light_panel_props:
        if item.light== obj:
            return False
    return True

class LightPanelProperties(bpy.types.PropertyGroup):
    open: bpy.props.BoolProperty(default=True)
    light: bpy.props.PointerProperty(
        name="Light",
        type=bpy.types.Object,
        poll=can_add_light,
    )
    type: bpy.props.EnumProperty(
        name="Light Node Type",
        description="The type of light node used in Godot",
        items=[
            ("DirectionalLight3D", "DirectionalLight3D", "A DirectionalLight3D is used in Godot"),
            ("OmniLight3D", "OmniLight3D", "An OmniLight3D is used in Godot"),
            ("SpotLight3D", "SpotLight3D", "A SpotLight3D is used in Godot"),
            ],
    )
    # omni specific settings
    omni_range: bpy.props.FloatProperty(
        name="Range",
        default=5.0
    )
    omni_attenuation: bpy.props.FloatProperty(
        name="Attenuation",
        default=1.0
    )
    omni_shadow_mode: bpy.props.EnumProperty(
        name="Shadow Mode",
        items=[
            ("0", "Dual Paraboloid", "Use Shadow Mode 'Dual Paraboloid' in Godot", 0),
            ("1", "Cube", "Use Shadow Mode 'Cube' in Godot", 1),
        ],
        default=1
    )
    # spot specific settings
    spot_range: bpy.props.FloatProperty(
        name="Range",
        default=5.0,
        subtype="DISTANCE"
    )
    spot_attenuation: bpy.props.FloatProperty(
        name="Attenuation",
        default=1.0
    )
    spot_angle: bpy.props.FloatProperty(
        name="Angle",
        default=radians(45.0),
        subtype="ANGLE"
    )
    spot_angle_attenuation: bpy.props.FloatProperty(
        name="Angle Attenuation",
        default=1.0
    )
    
    # general settings
    light_color: bpy.props.FloatVectorProperty(
        name="Color",
        size=3,
        subtype="COLOR_GAMMA",
        default=[1.0, 1.0, 1.0],
        min=0.0,
        max=1.0
    )
    light_energy: bpy.props.FloatProperty(
        name="Energy",
        default=1.0
    )
    light_indirect_energy: bpy.props.FloatProperty(
        name="Indirect Energy",
        default=1.0
    )
    light_volumetric_fog_energy: bpy.props.FloatProperty(
        name="Volumetric Fog Energy",
        default=1.0
    )
    light_angular_distance: bpy.props.FloatProperty(
        name="Angular Distance",
        default=0.0,
        subtype="ANGLE"
    )
    light_size: bpy.props.FloatProperty(
        name="Size",
        default=0.0,
        subtype="DISTANCE"
    )
    light_negative: bpy.props.BoolProperty(
        name="Negative",
        default=False
    )
    light_specular: bpy.props.FloatProperty(
        name="Specular",
        default=0.5 # default is 1.0 for DirectionalLight3D
    )
    light_bake_mode: bpy.props.EnumProperty(
        name="Bake Mode",
        items=[
            ("0", "Disabled", "Use Bake Mode 'Disabled' in Godot", 0),
            ("1", "Static", "Use Bake Mode 'Static' in Godot", 1),
            ("2", "Dynamic", "Use Bake Mode 'Dynamic' in Godot", 2)
        ],
        default=2
    )
    light_cull_mask: bpy.props.IntProperty(
        name="Cull Mask",
        default=1048575,
        subtype="UNSIGNED"
    )
    shadow_enabled: bpy.props.BoolProperty(
        name="Shadow",
        default=False
    )
