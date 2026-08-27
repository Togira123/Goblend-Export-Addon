# DefaultCollisionPanelProperties.py
#
# Copyright (C) 2026-present Goblend contributers, see https://github.com/Togira123/Goblend-Export-Addon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>


import bpy

from ...types import typed_prop_group, EnumProp, BoolProp, CollectionProp, IntProp
from ...ui.lists.DefaultCollisionLayersList import DefaultCollisionLayerListItem
from ...ui.lists.GroupList import GroupListItem
from ...ui.lists.CollisionMasksList import CollisionMaskListItem

from .enum_items import physics_objects


@typed_prop_group
class DefaultCollisionPanelProperties(bpy.types.PropertyGroup):
    type = EnumProp(
        name="Default Physics Object",
        description="Default type of Physics Object to use",
        items=physics_objects,
        default="STATIC_BODY",
    )
    use_layer_config_value = BoolProp(name="Use Config Default Value", default=True)
    default_layers_panel_open = BoolProp(default=True)
    default_layers_list = CollectionProp(type=DefaultCollisionLayerListItem)
    default_layers_list_index = IntProp()

    use_mask_config_value = BoolProp(name="Use Config Default Value", default=True)
    default_masks_panel_open = BoolProp(default=True)
    default_masks_list = CollectionProp(type=CollisionMaskListItem)
    default_masks_list_index = IntProp()

    default_groups_panel_open = BoolProp(default=True)
    default_groups_list = CollectionProp(type=GroupListItem)
    default_groups_list_index = IntProp()
