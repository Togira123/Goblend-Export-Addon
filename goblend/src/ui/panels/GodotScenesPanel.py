import bpy


class SCENE_PT_GodotScenesPanel(bpy.types.Panel):
    bl_parent_id = "SCENE_PT_export_to_godot"
    bl_label = "Godot Scenes"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        godot_scene_panel_props = scene.godot_scene_panel_props

        layout.use_property_split = True
        layout.use_property_decorate = False

        for item in godot_scene_panel_props:
            header, panel = layout.panel_prop(item, "open")

            split = header.split()

            col = split.column()

            obj_name = item.obj.name if item.obj else "No Object"

            col.label(text=obj_name)

            row = split.row()
            row.alignment = "RIGHT"
            row.context_pointer_set(name="godot_scene_to_remove", data=item.obj)
            row.operator("scene.remove_godot_scene_setting", text="", icon="X", emboss=False)

            if panel:
                panel.use_property_split = True
                col = panel.column()
                col.prop(item, "obj")
                col.prop(item, "scene")
