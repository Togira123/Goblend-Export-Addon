# CollisionLayersList.py
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


from typing import cast, TYPE_CHECKING

import bpy

if TYPE_CHECKING:
    from ..property_groups.CollisionPanelProperties import CollisionPanelProperties
from ... import config as conf
from ... import utils

from ...types.property_types import typed_prop_group, BoolProp, EnumProp
from ...types.blender_types import OperatorReturnItems


def layer_items(
    _self: bpy.types.Operator | type[bpy.types.Operator], _context: bpy.types.Context | None
) -> list[tuple[str, str, str]]:
    if len(utils.layers_enum_cache) == 0:
        config = conf.get_config()
        for layer in config["collisions"]["layers"]:
            utils.layers_enum_cache.append((str(layer["bit"]), layer["display_name"], "Bit " + str(layer["bit"])))

    return utils.layers_enum_cache


@typed_prop_group
class CollisionLayerListItem(bpy.types.PropertyGroup):
    enabled = BoolProp(name="Enable", description="Enable or disable this layer", default=True)
    force_disabled = BoolProp(
        name="Force Disabled", description="There exists another override for this layer already", default=False
    )
    layer = EnumProp(
        name="Layer",
        items=layer_items,
    )


class SCENE_UL_CollisionLayersList(bpy.types.UIList):
    def draw_item(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout,
        data: "CollisionPanelProperties | None",
        item: CollisionLayerListItem | None,
        icon: int | None,
        active_data: "CollisionPanelProperties",
        active_property: str | None,
        index: int | None,
        flt_flag: int | None,
    ) -> None:
        split = layout.split()
        row = split.row()
        col1 = row.row()
        duplicate = False
        if not data or not item:
            return
        if not index:
            index = 0
        for i in range(index):
            if data.layers_override_list[i].layer == item.layer:
                # another one before has the same prop, disable
                duplicate = True
                break
        col1.enabled = not duplicate
        if duplicate:
            col1.prop(item, "force_disabled", text="")
        else:
            col1.prop(item, "enabled", text="")
        col1.alignment = "RIGHT"
        col2 = row.row()
        col2.enabled = item.enabled
        col2.prop(item, "layer", text="")


class CollisionLayersListContext(bpy.types.Context):
    list: "CollisionPanelProperties"


class LIST_OT_AddItemToLayersList(bpy.types.Operator):
    bl_idname = "collision_layers_list.add_item"
    bl_label = "Add a layer"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return len(cast(CollisionLayersListContext, context).list.layers_override_list) < len(layer_items(cls, context))

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        ctx = cast(CollisionLayersListContext, context)
        # find first unused layer
        existing: set[str] = set()
        for override in ctx.list.layers_override_list:
            existing.add(override.layer)
        item = ctx.list.layers_override_list.add()
        all_layers = layer_items(self, context)
        for layer in all_layers:
            if layer[0] not in existing:
                item.layer = layer[0]
                break
        return {"FINISHED"}


class LIST_OT_RemoveItemFromLayersList(bpy.types.Operator):
    bl_idname = "collision_layers_list.remove_item"
    bl_label = "Remove a layer"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return len(cast(CollisionLayersListContext, context).list.layers_override_list) > 0

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        ctx = cast(CollisionLayersListContext, context)
        li = ctx.list.layers_override_list
        index = ctx.list.layers_list_index
        li.remove(index)
        ctx.list.layers_list_index = min(max(0, index - 1), len(li) - 1)

        return {"FINISHED"}
