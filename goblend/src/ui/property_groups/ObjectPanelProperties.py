import bpy

from .enum_items import shadow_cast_enum_items


def can_add_object_constraint(self, object):
    scene = bpy.context.scene
    if object.type != "MESH":
        return False
    if object.library != None:
        return False
    collision_collection = bpy.data.collections.get("Collisions")
    if collision_collection and object.name in collision_collection.all_objects:
        return False
    for item in scene.object_panel_props:
        if item.obj == object:
            return False
    return True


class ObjectPanelProperties(bpy.types.PropertyGroup):
    open: bpy.props.BoolProperty(default=True)
    obj: bpy.props.PointerProperty(
        name="Object",
        type=bpy.types.Object,
        poll=can_add_object_constraint,
    )
    enabled: bpy.props.BoolProperty(
        name="Enable Constraint", description="Whether this constraint should be enabled", default=True
    )

    def uvmaps(self, context):
        if self.obj:
            return [(uv.name, uv.name, "") for uv in self.obj.data.uv_layers][:8]  # godot only allows up to 8 uv maps
        return []

    uv_map_enabled: bpy.props.BoolProperty(
        name="Override UV Map", description="Whether to use a separate UV Map as bake target", default=False
    )

    uv_map_per_texture_enabled: bpy.props.BoolProperty(
        name="Per Texture", description="Whether to use a different UV map per texture", default=False
    )

    uv_map: bpy.props.EnumProperty(name="UV Map", items=uvmaps)
    uv_map_base_color: bpy.props.EnumProperty(name="Base Color", items=uvmaps)
    uv_map_metallic_roughness: bpy.props.EnumProperty(name="Metallic/Roughness", items=uvmaps)
    uv_map_normal: bpy.props.EnumProperty(name="Normal", items=uvmaps)

    shadow_cast_mode: bpy.props.EnumProperty(
        name="Shadow Cast Mode",
        description="These are the options that 'cast_shadow' has in Godot on a GeometryInstance3D",
        items=shadow_cast_enum_items,
        default="ON",
    )
