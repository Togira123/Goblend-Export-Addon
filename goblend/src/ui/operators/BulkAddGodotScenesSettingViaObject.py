# BulkAddGodotScenesSettingViaObject.py
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

from ...types.goblend_types import GoblendScene

from ...types.property_types import StringProp, typed_prop_group

from ...types.blender_types import OperatorReturnItems
from ..property_groups.GodotScenePanelProperties import scenes

import bpy


@typed_prop_group
class OUTLINER_OT_BulkAddGodotScenesSettingViaObject(bpy.types.Operator):
    bl_idname = "outliner.bulk_add_godot_scene_setting_via_object"
    bl_label = "Add Object as Godot Scene"
    bl_description = "Replace this object by an existing Godot scene on export"

    scene_name = StringProp()

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        selected_objects = [id for id in context.selected_ids if isinstance(id, bpy.types.Object)]
        # this is much slower than a simple bpy.data.collections.get("bpy.context.scene.panel_props.godot_scenes_collection"),
        # but it only includes collections of the current scene
        # it shouldn't matter too much with a low collection count
        scene: GoblendScene = context.scene
        all_collections_in_scene = scene.collection.children_recursive if scene else []
        godot_scenes: bpy.types.Collection | None = None
        for coll in all_collections_in_scene:
            if coll.name == bpy.context.scene.panel_props.godot_scenes_collection:
                godot_scenes = coll
                break

        if not godot_scenes:
            return {"CANCELLED"}
        all_child_collections = godot_scenes.children_recursive if godot_scenes else []
        # take all objects in godot_scenes collection into account (also indirect children)
        all_objects_in_godot_scenes_collection: set[bpy.types.Object] = set(godot_scenes.objects)
        for coll in all_child_collections:
            all_objects_in_godot_scenes_collection.update(coll.objects)
        already_existing_objects = dict([(s.obj.name, s) for s in scene.godot_scene_panel_props.values() if s.obj])
        for obj in selected_objects:
            # it has to be an object inside of a child collection of the GodotScenes collection
            if obj in all_objects_in_godot_scenes_collection:
                if obj.name in already_existing_objects:
                    panel = already_existing_objects.get(obj.name)
                    if panel:
                        panel.scene = self.scene_name
                else:
                    new_panel = scene.godot_scene_panel_props.add()
                    new_panel.obj = obj
                    new_panel.scene = self.scene_name
        # we have to redraw the panels, otherwise they won't update until hovered/clicked
        wm: bpy.types.WindowManager | None = context.window_manager
        if wm:
            for window in wm.windows:
                for area in window.screen.areas:
                    if area.type == "PROPERTIES":
                        area.tag_redraw()
        return {"FINISHED"}


class OUTLINER_MT_BulkAddGodotScenesSettingViaObject(bpy.types.Menu):
    bl_idname = "OUTLINER_MT_BulkAddGodotScenesSettingViaObject"
    bl_label = "Add Object as Godot Scene"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        if layout:
            godot_scenes = scenes()
            for scene in godot_scenes:
                layout.operator("outliner.bulk_add_godot_scene_setting_via_object", text=scene[1]).scene_name = scene[0]


def draw_bulk_add_godot_scenes_setting_via_object_menu(self: bpy.types.Menu, context: bpy.types.Context) -> None:
    layout = self.layout
    obj_of_menu = context.object
    if layout and obj_of_menu:
        # this is much slower than a simple bpy.data.collections.get("bpy.context.scene.panel_props.godot_scenes_collection"),
        # but it only includes collections of the current scene
        # it shouldn't matter too much with a low collection count
        scene: GoblendScene = context.scene
        all_collections_in_scene = scene.collection.children_recursive if scene else []
        godot_scenes: bpy.types.Collection | None = None
        for coll in all_collections_in_scene:
            if coll.name == bpy.context.scene.panel_props.godot_scenes_collection:
                godot_scenes = coll
                break
        if not godot_scenes:
            return
        all_child_collections = godot_scenes.children_recursive if godot_scenes else []
        # take all objects in godot_scenes collection into account (also indirect children)
        all_objects_in_godot_scenes_collection: set[bpy.types.Object] = set(godot_scenes.objects)
        for coll in all_child_collections:
            all_objects_in_godot_scenes_collection.update(coll.objects)
            # only show the menu if we right clicked an object inside a godot scenes collection
        if obj_of_menu in all_objects_in_godot_scenes_collection:
            layout.separator()
            layout.menu("OUTLINER_MT_BulkAddGodotScenesSettingViaObject")
