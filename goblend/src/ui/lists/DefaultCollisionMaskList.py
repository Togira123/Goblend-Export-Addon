import bpy
from .CollisionLayersList import layer_items


class DefaultCollisionMaskListItem(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(name="Enable", description="Enable or disable this mask", default=True)
    force_disabled: bpy.props.BoolProperty(
        name="Force Disabled", description="There exists another entry for this mask already", default=False
    )
    mask: bpy.props.EnumProperty(
        name="Mask",
        items=layer_items,
    )


class SCENE_UL_DefaultCollisionMasksList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split()
        row = split.row()
        col1 = row.row()
        duplicate = False
        for i in range(index):
            if data.default_masks_list[i].mask == item.mask:
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


class LIST_OT_AddItemToDefaultMasksList(bpy.types.Operator):
    bl_idname = "default_collision_masks_list.add_item"
    bl_label = "Add a mask"

    @classmethod
    def poll(cls, context):
        return len(context.scene.default_collision_panel_props.default_masks_list) < len(layer_items(cls, context))

    def execute(self, context):
        # find first unused mask
        existing = set()
        for override in context.scene.default_collision_panel_props.default_masks_list:
            existing.add(override.mask)
        item = context.scene.default_collision_panel_props.default_masks_list.add()
        all_masks = layer_items(self, context)
        for mask in all_masks:
            if not mask[0] in existing:
                item.mask = mask[0]
                break
        return {"FINISHED"}


class LIST_OT_RemoveItemFromDefaultMasksList(bpy.types.Operator):
    bl_idname = "default_collision_masks_list.remove_item"
    bl_label = "Remove a mask"

    @classmethod
    def poll(cls, context):
        return context.scene.default_collision_panel_props.default_masks_list

    def execute(self, context):
        li = context.scene.default_collision_panel_props.default_masks_list
        index = context.scene.default_collision_panel_props.default_masks_list_index
        li.remove(index)
        context.scene.default_collision_panel_props.default_masks_list_index = min(max(0, index - 1), len(li) - 1)

        return {"FINISHED"}
