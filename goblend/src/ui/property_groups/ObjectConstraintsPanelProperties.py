import bpy

from .MaterialOverrideProperties import MaterialOverrideProperties

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
    for item in scene.object_constraints_panel_props:
        if item.obj == object:
            return False
    return True

def on_update(self, _context):
    for override in self.material_overrides:
        override.mat = None
        override.obj = self.obj


class ObjectConstraintsPanelProperties(bpy.types.PropertyGroup):
    open: bpy.props.BoolProperty(default=True)
    obj: bpy.props.PointerProperty(
        name="Object",
        type=bpy.types.Object,
        poll=can_add_object_constraint,
        update=on_update
    )
    enabled: bpy.props.BoolProperty(
        name="Enable Constraint",
        description="Whether this constraint should be enabled",
        default=True
    )
    
    uv_group: bpy.props.StringProperty(
        name="UV Group",
        description="Objects with the same UV Group will bake textures to the same image file",
        default=""
    )
    
    shadow_cast_mode: bpy.props.EnumProperty(
        name="Shadow Cast Mode",
        description="These are the options that 'cast_shadow' has in Godot on a GeometryInstance3D",
        items=shadow_cast_enum_items,
        default="ON"
    )
    
    material_overrides: bpy.props.CollectionProperty(type=MaterialOverrideProperties)
