import bpy


class SCENE_PT_CollisionsPanel(bpy.types.Panel):
    bl_parent_id = "SCENE_PT_export_to_godot"
    bl_label = "Collisions"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        collision_panel_props = scene.collision_panel_props

        layout.use_property_split = True
        layout.use_property_decorate = False

        for item in collision_panel_props:
            header, panel = layout.panel_prop(item, "open")

            split = header.split()

            col = split.column()

            collision_name = item.collection.name if item.collection else "No Collection"

            col.label(text=collision_name)

            row = split.row()
            row.alignment = "RIGHT"
            row.context_pointer_set(name="collision_collection_to_remove", data=item.collection)
            row.operator("scene.remove_collision_setting", text="", icon="X", emboss=False)

            if panel:
                panel.use_property_split = True
                col = panel.column()
                col.prop(item, "collection")
                col.prop(item, "type")

                col.prop(item, "layers_override_enabled")
                if item.layers_override_enabled:
                    layers_override_header, layers_override_panel = panel.panel_prop(item, "layers_override_panel_open")
                    layers_override_header.label(text="Layer Overrides")
                    if layers_override_panel:
                        row = layers_override_panel.row()
                        row.template_list(
                            "SCENE_UL_CollisionLayersList",
                            "layers_list",
                            item,
                            "layers_override_list",
                            item,
                            "layers_list_index",
                        )

                        inner_col = row.column(align=True)
                        inner_col.context_pointer_set(name="list", data=item)
                        inner_col.operator("collision_layers_list.add_item", icon="ADD", text="")
                        inner_col.operator("collision_layers_list.remove_item", icon="REMOVE", text="")

                col.prop(item, "masks_override_enabled")
                if item.masks_override_enabled:
                    masks_override_header, masks_override_panel = panel.panel_prop(item, "masks_override_panel_open")
                    masks_override_header.label(text="Mask Overrides")
                    if masks_override_panel:
                        row = masks_override_panel.row()
                        row.template_list(
                            "SCENE_UL_CollisionMasksList",
                            "masks_list",
                            item,
                            "masks_override_list",
                            item,
                            "masks_list_index",
                        )

                        inner_col = row.column(align=True)
                        inner_col.context_pointer_set(name="list", data=item)
                        inner_col.operator("collision_masks_list.add_item", icon="ADD", text="")
                        inner_col.operator("collision_masks_list.remove_item", icon="REMOVE", text="")

                col.prop(item, "groups_override_enabled")
                if item.groups_override_enabled:
                    groups_override_header, groups_override_panel = panel.panel_prop(item, "groups_override_panel_open")
                    groups_override_header.label(text="Group Overrides")
                    if groups_override_panel:
                        row = groups_override_panel.row()
                        row.template_list(
                            "SCENE_UL_GroupsList",
                            "groups_list",
                            item,
                            "groups_override_list",
                            item,
                            "groups_list_index",
                        )

                        inner_col = row.column(align=True)
                        inner_col.context_pointer_set(name="list", data=item)
                        inner_col.operator("groups_list.add_item", icon="ADD", text="")
                        inner_col.operator("groups_list.remove_item", icon="REMOVE", text="")
