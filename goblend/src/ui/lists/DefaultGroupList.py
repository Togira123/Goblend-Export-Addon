import bpy
from .GroupList import group_items


class DefaultGroupListItem(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(name="Enable", description="Enable or disable this group", default=True)
    force_disabled: bpy.props.BoolProperty(
        name="Force Disabled", description="There exists another entry for this group already", default=False
    )
    group: bpy.props.EnumProperty(
        name="Group",
        items=group_items,
    )


class SCENE_UL_DefaultGroupList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split()
        row = split.row()
        col1 = row.row()
        duplicate = False
        for i in range(index):
            if data.default_groups_list[i].group == item.group:
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


class LIST_OT_AddItemToDefaultGroupList(bpy.types.Operator):
    bl_idname = "default_group_list.add_item"
    bl_label = "Add a group"

    @classmethod
    def poll(cls, context):
        return len(context.scene.default_collision_panel_props.default_groups_list) < len(group_items(cls, context))

    def execute(self, context):
        # find first unused mask
        existing = set()
        for override in context.scene.default_collision_panel_props.default_groups_list:
            existing.add(override.group)
        item = context.scene.default_collision_panel_props.default_groups_list.add()
        all_groups = group_items(self, context)
        for group in all_groups:
            if not group[0] in existing:
                item.group = group[0]
                break
        return {"FINISHED"}


class LIST_OT_RemoveItemFromDefaultGroupList(bpy.types.Operator):
    bl_idname = "default_group_list.remove_item"
    bl_label = "Remove a group"

    @classmethod
    def poll(cls, context):
        return context.scene.default_collision_panel_props.default_groups_list

    def execute(self, context):
        li = context.scene.default_collision_panel_props.default_groups_list
        index = context.scene.default_collision_panel_props.default_groups_list_index
        li.remove(index)
        context.scene.default_collision_panel_props.default_groups_list_index = min(max(0, index - 1), len(li) - 1)

        return {"FINISHED"}
