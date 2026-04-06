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


import bpy

from ... import config as conf
from ... import utils


def group_items(_self, _context):
    if len(utils.group_list_enum_cache) == 0:
        config = conf.get_config()
        for group in config["collisions"]["groups"]:
            utils.group_list_enum_cache.append(
                (str(group["godot_group_name"]), group["display_name"], group["description"])
            )
    return utils.group_list_enum_cache


class GroupListItem(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(name="Enabled", description="Enable or disable this group", default=True)
    force_disabled: bpy.props.BoolProperty(
        name="Force Disabled", description="There exists another override for this group already", default=False
    )
    group: bpy.props.EnumProperty(name="Group", items=group_items)


class SCENE_UL_GroupsList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split()
        row = split.row()
        col1 = row.row()
        duplicate = False
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


class LIST_OT_AddItemToGroupsList(bpy.types.Operator):
    bl_idname = "groups_list.add_item"
    bl_label = "Add a group"

    @classmethod
    def poll(cls, context):
        return len(context.list.groups_override_list) < len(group_items(cls, context))

    def execute(self, context):
        # find first unused group
        existing = set()
        for override in context.list.groups_override_list:
            existing.add(override.group)
        item = context.list.groups_override_list.add()
        all_groups = group_items(self, context)
        for group in all_groups:
            if not group[0] in existing:
                item.group = group[0]
                break
        return {"FINISHED"}


class LIST_OT_RemoveItemFromGroupsList(bpy.types.Operator):
    bl_idname = "groups_list.remove_item"
    bl_label = "Remove a group"

    @classmethod
    def poll(cls, context):
        return context.list.groups_override_list

    def execute(self, context):
        li = context.list.groups_override_list
        index = context.list.groups_list_index
        li.remove(index)
        context.list.groups_list_index = min(max(0, index - 1), len(li) - 1)

        return {"FINISHED"}
