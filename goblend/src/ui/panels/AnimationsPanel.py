import bpy


class SCENE_PT_AnimationsPanel(bpy.types.Panel):
    bl_parent_id = "SCENE_PT_export_to_godot"
    bl_label = "Animations"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        animation_panel_props = scene.animation_panel_props

        layout.use_property_split = True
        layout.use_property_decorate = False

        for item in animation_panel_props:
            header, panel = layout.panel_prop(item, "open")

            split = header.split()

            col = split.column()

            animation_name = item.animation.name if item.animation else "No Animation"

            col.label(text=animation_name)

            row = split.row()
            row.alignment = "RIGHT"
            row.context_pointer_set(name="animation_to_remove", data=item.animation)
            row.operator("scene.remove_animation_setting", text="", icon="X", emboss=False)

            if panel:
                panel.use_property_split = True
                col = panel.column()
                col.prop(item, "animation")
                col.prop(item, "loop")
                col.prop(item, "autoplay")
