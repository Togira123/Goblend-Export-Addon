# GroupList.py
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

from ...types.blender_types import OperatorReturnItems

from ... import config as conf
from ... import utils

from ...types.property_types import typed_prop_group, BoolProp, EnumProp

if TYPE_CHECKING:
    from ..property_groups.CollisionPanelProperties import CollisionPanelProperties


def group_items(
    _self: type[bpy.types.Operator] | bpy.types.Operator, _context: bpy.types.Context | None
) -> list[tuple[str, str, str]]:
    if len(utils.group_list_enum_cache) == 0:
        config = conf.get_config()
        for group in config["collisions"]["groups"]:
            utils.group_list_enum_cache.append(
                (str(group["godot_group_name"]), group["display_name"], group["description"])
            )
    return utils.group_list_enum_cache


@typed_prop_group
class GroupListItem(bpy.types.PropertyGroup):
    enabled = BoolProp(name="Enabled", description="Enable or disable this group", default=True)
    force_disabled = BoolProp(
        name="Force Disabled", description="There exists another override for this group already", default=False
    )
    group = EnumProp(name="Group", items=group_items)


class SCENE_UL_GroupsList(bpy.types.UIList):
    def draw_item(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout,
        data: "CollisionPanelProperties | None",
        item: GroupListItem | None,
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
            if data.groups_override_list[i].group == item.group:
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
        col2.prop(item, "group", text="")


class GroupListContext(bpy.types.Context):
    list: "CollisionPanelProperties"


class LIST_OT_AddItemToGroupsList(bpy.types.Operator):
    bl_idname = "groups_list.add_item"
    bl_label = "Add a group"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return len(cast(GroupListContext, context).list.groups_override_list) < len(group_items(cls, context))

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        ctx = cast(GroupListContext, context)
        # find first unused group
        existing: set[str] = set()
        for override in ctx.list.groups_override_list:
            existing.add(override.group)
        item = ctx.list.groups_override_list.add()
        all_groups = group_items(self, context)
        for group in all_groups:
            if group[0] not in existing:
                item.group = group[0]
                break
        return {"FINISHED"}


class LIST_OT_RemoveItemFromGroupsList(bpy.types.Operator):
    bl_idname = "groups_list.remove_item"
    bl_label = "Remove a group"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return len(cast(GroupListContext, context).list.groups_override_list) > 0

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        ctx = cast(GroupListContext, context)
        li = ctx.list.groups_override_list
        index = ctx.list.groups_list_index
        li.remove(index)
        ctx.list.groups_list_index = min(max(0, index - 1), len(li) - 1)

        return {"FINISHED"}
