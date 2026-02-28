import bpy

from ...config import get_config
from ...ui.lists.CollisionLayersList import layer_items


class CollisionMaskListItem(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(name="Enable", description="Enable or disable this mask", default=True)
    force_disabled: bpy.props.BoolProperty(
        name="Force Disabled", description="There exists another override for this mask already", default=False
    )
    mask: bpy.props.EnumProperty(name="Mask", items=layer_items)


class SCENE_UL_CollisionMasksList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split()
        row = split.row()
        col1 = row.row()
        duplicate = False
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


class LIST_OT_AddItemToMasksList(bpy.types.Operator):
    bl_idname = "collision_masks_list.add_item"
    bl_label = "Add a mask"

    @classmethod
    def poll(cls, context):
        return len(context.list.masks_override_list) < len(layer_items(cls, context))

    def execute(self, context):
        # find first unused mask
        existing = set()
        for override in context.list.masks_override_list:
            existing.add(override.mask)
        item = context.list.masks_override_list.add()
        all_masks = layer_items(self, context)
        for mask in all_masks:
            if not mask[0] in existing:
                item.mask = mask[0]
                break
        return {"FINISHED"}


class LIST_OT_RemoveItemFromMasksList(bpy.types.Operator):
    bl_idname = "collision_masks_list.remove_item"
    bl_label = "Remove a mask"

    @classmethod
    def poll(cls, context):
        return context.list.masks_override_list

    def execute(self, context):
        li = context.list.masks_override_list
        index = context.list.masks_list_index
        li.remove(index)
        context.list.masks_list_index = min(max(0, index - 1), len(li) - 1)
        return {"FINISHED"}
