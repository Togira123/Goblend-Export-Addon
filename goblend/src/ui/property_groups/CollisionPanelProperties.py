# CollisionPanelProperties.py
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
from ...ui.lists.GroupList import GroupListItem
from ...ui.lists.CollisionLayersList import CollisionLayerListItem
from ...ui.lists.CollisionMasksList import CollisionMaskListItem

from .enum_items import physics_objects

from ...types import BoolProp, PointerProp, EnumProp, CollectionProp, IntProp, typed_prop_group


def is_collision_collection(self: bpy.types.PropertyGroup, collection: bpy.types.Collection) -> bool:
    scene = bpy.context.scene
    existing: list[bpy.types.Collection] = []
    for item in scene.collision_panel_props:
        existing.append(item.collection)
    # this is much slower than a simple bpy.data.collections.get(bpy.context.scene.panel_props.collision_collection),
    # but it only includes collections of the current scene
    # it shouldn't matter too much with a low collection count
    all_collections_in_scene = scene.collection.children_recursive
    collision_collection: bpy.types.Collection | None = None
    for coll in all_collections_in_scene:
        if coll.name == bpy.context.scene.panel_props.collision_collection:
            collision_collection = coll
            break
    return (
        collection == collision_collection
        or (collision_collection is not None and collection in collision_collection.children_recursive)
    ) and collection not in existing


@typed_prop_group
class CollisionPanelProperties(bpy.types.PropertyGroup):
    open = BoolProp(default=True)
    collection = PointerProp(name="Collection", type=bpy.types.Collection, poll=is_collision_collection)
    type = EnumProp(
        name="Physics Object",
        description="Type of Physics Object to use for this collection",
        items=physics_objects,
        default="STATIC_BODY",
    )
    layers_override_enabled = BoolProp(name="Override Collision Layers", default=False)
    layers_override_panel_open = BoolProp(default=True)
    layers_override_list = CollectionProp(type=CollisionLayerListItem)
    layers_list_index = IntProp()

    masks_override_enabled = BoolProp(name="Override Collision Masks", default=False)
    masks_override_panel_open = BoolProp(default=True)
    masks_override_list = CollectionProp(type=CollisionMaskListItem)
    masks_list_index = IntProp()

    groups_override_enabled = BoolProp(name="Override Groups", default=False)
    groups_override_panel_open = BoolProp(default=True)
    groups_override_list = CollectionProp(type=GroupListItem)
    groups_list_index = IntProp()
