import bpy
from ...ui.lists.GroupList import GroupListItem
from ...ui.lists.CollisionLayersList import CollisionLayerListItem
from ...ui.lists.CollisionMasksList import CollisionMaskListItem

from .enum_items import physics_objects


def is_collision_collection(self, collection):
    scene = bpy.context.scene
    existing = []
    for item in scene.collision_panel_props:
        existing.append(item.collection)
    collision_collection = bpy.data.collections.get("Collisions")
    return (
        collection == collision_collection or collection in collision_collection.children_recursive
    ) and not collection in existing


class CollisionPanelProperties(bpy.types.PropertyGroup):
    open: bpy.props.BoolProperty(default=True)
    collection: bpy.props.PointerProperty(name="Collection", type=bpy.types.Collection, poll=is_collision_collection)
    type: bpy.props.EnumProperty(
        name="Physics Object",
        description="Type of Physics Object to use for this collection",
        items=physics_objects,
        default="STATIC_BODY",
    )
    layers_override_enabled: bpy.props.BoolProperty(name="Override Collision Layers", default=False)
    layers_override_panel_open: bpy.props.BoolProperty(default=True)
    layers_override_list: bpy.props.CollectionProperty(type=CollisionLayerListItem)
    layers_list_index: bpy.props.IntProperty()

    masks_override_enabled: bpy.props.BoolProperty(name="Override Collision Masks", default=False)
    masks_override_panel_open: bpy.props.BoolProperty(default=True)
    masks_override_list: bpy.props.CollectionProperty(type=CollisionMaskListItem)
    masks_list_index: bpy.props.IntProperty()

    groups_override_enabled: bpy.props.BoolProperty(name="Override Groups", default=False)
    groups_override_panel_open: bpy.props.BoolProperty(default=True)
    groups_override_list: bpy.props.CollectionProperty(type=GroupListItem)
    groups_list_index: bpy.props.IntProperty()
