# CollisionMasksList.py
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

from typing import cast, TYPE_CHECKING

from ...types.blender_types import OperatorReturnItems

if TYPE_CHECKING:
    from ..property_groups.CollisionPanelProperties import CollisionPanelProperties

from ...types.property_types import typed_prop_group, BoolProp, EnumProp

from .CollisionLayersList import layer_items


@typed_prop_group
class CollisionMaskListItem(bpy.types.PropertyGroup):
    enabled = BoolProp(name="Enable", description="Enable or disable this mask", default=True)
    force_disabled = BoolProp(
        name="Force Disabled", description="There exists another override for this mask already", default=False
    )
    mask = EnumProp(name="Mask", items=layer_items)


class SCENE_UL_CollisionMasksList(bpy.types.UIList):
    def draw_item(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout,
        data: "CollisionPanelProperties | None",
        item: CollisionMaskListItem | None,
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
            if data.masks_override_list[i].mask == item.mask:
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
        col2.prop(item, "mask", text="")


class CollisionMasksListContext(bpy.types.Context):
    list: "CollisionPanelProperties"


class LIST_OT_AddItemToMasksList(bpy.types.Operator):
    bl_idname = "collision_masks_list.add_item"
    bl_label = "Add a mask"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return len(cast(CollisionMasksListContext, context).list.masks_override_list) < len(layer_items(cls, context))

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        ctx = cast(CollisionMasksListContext, context)
        # find first unused mask
        existing: set[str] = set()
        for override in ctx.list.masks_override_list:
            existing.add(override.mask)
        item = ctx.list.masks_override_list.add()
        all_masks = layer_items(self, context)
        for mask in all_masks:
            if mask[0] not in existing:
                item.mask = mask[0]
                break
        return {"FINISHED"}


class LIST_OT_RemoveItemFromMasksList(bpy.types.Operator):
    bl_idname = "collision_masks_list.remove_item"
    bl_label = "Remove a mask"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return len(cast(CollisionMasksListContext, context).list.masks_override_list) > 0

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        ctx = cast(CollisionMasksListContext, context)
        li = ctx.list.masks_override_list
        index = ctx.list.masks_list_index
        li.remove(index)
        ctx.list.masks_list_index = min(max(0, index - 1), len(li) - 1)
        return {"FINISHED"}
