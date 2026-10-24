# BulkAddGodotScenesSettingViaCollection.py
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
class OUTLINER_OT_BulkAddGodotScenesSettingViaCollection(bpy.types.Operator):
    bl_idname = "outliner.bulk_add_godot_scene_setting_via_collection"
    bl_label = "Add Child Objects as Godot Scene"
    bl_description = "Replace all child objects by an existing Godot scene on export"

    scene_name = StringProp()

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        selected_collections = [id for id in context.selected_ids if isinstance(id, bpy.types.Collection)]
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
        all_child_collections = godot_scenes.children_recursive if godot_scenes else []
        already_existing_objects = dict([(s.obj.name, s) for s in scene.godot_scene_panel_props.values() if s.obj])
        for coll in selected_collections:
            # it has to be a child collection of the GodotScenes collection
            if coll in all_child_collections or coll == godot_scenes:
                for obj in coll.objects:
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


class OUTLINER_MT_BulkAddGodotScenesSettingViaCollection(bpy.types.Menu):
    bl_idname = "OUTLINER_MT_BulkAddGodotScenesSettingViaCollection"
    bl_label = "Add Child Objects as Godot Scene"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        if layout:
            godot_scenes = scenes()
            for scene in godot_scenes:
                layout.operator("outliner.bulk_add_godot_scene_setting_via_collection", text=scene[1]).scene_name = (
                    scene[0]
                )


def draw_bulk_add_godot_scenes_setting_via_collection_menu(self: bpy.types.Menu, context: bpy.types.Context) -> None:
    layout = self.layout
    coll_of_menu: bpy.types.Collection | None = context.collection
    if layout and coll_of_menu:
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
        all_child_collections = godot_scenes.children_recursive if godot_scenes else []
        # only show the menu if we right clicked a godot scenes collection
        if coll_of_menu == godot_scenes or coll_of_menu in all_child_collections:
            layout.separator()
            layout.menu("OUTLINER_MT_BulkAddGodotScenesSettingViaCollection")
