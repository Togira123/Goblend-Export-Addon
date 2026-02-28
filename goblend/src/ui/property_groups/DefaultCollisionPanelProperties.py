import bpy
from ...ui.lists.DefaultCollisionLayersList import DefaultCollisionLayerListItem
from ...ui.lists.GroupList import GroupListItem
from ...ui.lists.CollisionMasksList import CollisionMaskListItem

from .enum_items import physics_objects


class DefaultCollisionPanelProperties(bpy.types.PropertyGroup):
    type: bpy.props.EnumProperty(
        name="Default Physics Object",
        description="Default type of Physics Object to use",
        items=physics_objects,
        default="STATIC_BODY",
    )
    use_layer_config_value: bpy.props.BoolProperty(name="Use Config Default Value", default=True)
    default_layers_panel_open: bpy.props.BoolProperty(default=True)
    default_layers_list: bpy.props.CollectionProperty(type=DefaultCollisionLayerListItem)
    default_layers_list_index: bpy.props.IntProperty()

    use_mask_config_value: bpy.props.BoolProperty(name="Use Config Default Value", default=True)
    default_masks_panel_open: bpy.props.BoolProperty(default=True)
    default_masks_list: bpy.props.CollectionProperty(type=CollisionMaskListItem)
    default_masks_list_index: bpy.props.IntProperty()

    default_groups_panel_open: bpy.props.BoolProperty(default=True)
    default_groups_list: bpy.props.CollectionProperty(type=GroupListItem)
    default_groups_list_index: bpy.props.IntProperty()
