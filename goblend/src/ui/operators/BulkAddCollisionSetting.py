# BulkAddCollisionSetting.py
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

from ..property_groups.enum_items import physics_objects

import bpy


@typed_prop_group
class OUTLINER_OT_BulkAddCollisionSetting(bpy.types.Operator):
    bl_idname = "outliner.bulk_add_collision_setting"
    bl_label = "Add a Collision Setting for Collection"
    bl_description = "Customize how this collection is handled for collisions in Godot"

    physics_type = StringProp()

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        selected_collections = [id for id in context.selected_ids if isinstance(id, bpy.types.Collection)]
        scene: GoblendScene = context.scene
        # this is much slower than a simple bpy.data.collections.get(bpy.context.scene.panel_props.collision_collection),
        # but it only includes collections of the current scene
        # it shouldn't matter too much with a low collection count
        all_collections_in_scene = scene.collection.children_recursive if scene else []
        collision_collection: bpy.types.Collection | None = None
        for coll in all_collections_in_scene:
            if coll.name == bpy.context.scene.panel_props.collision_collection:
                collision_collection = coll
                break
        all_child_collections = collision_collection.children_recursive if collision_collection else []
        already_existing_collections = dict(
            [(s.collection.name, s) for s in scene.collision_panel_props.values() if s.collection]
        )
        for coll in selected_collections:
            # it has to be a child collection of the Collisions collection
            if coll in all_child_collections or coll == collision_collection:
                if coll.name in already_existing_collections:
                    panel = already_existing_collections.get(coll.name)
                    if panel:
                        panel.type = self.physics_type
                else:
                    new_panel = scene.collision_panel_props.add()
                    new_panel.collection = coll
                    new_panel.type = self.physics_type
        # we have to redraw the panels, otherwise they won't update until hovered/clicked
        wm: bpy.types.WindowManager | None = context.window_manager
        if wm:
            for window in wm.windows:
                for area in window.screen.areas:
                    if area.type == "PROPERTIES":
                        area.tag_redraw()
        return {"FINISHED"}


class OUTLINER_MT_BulkAddCollisionSetting(bpy.types.Menu):
    bl_idname = "OUTLINER_MT_BulkAddCollisionSetting"
    bl_label = "Add a Collision Setting for Collection"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        if layout:
            for physics_object in physics_objects:
                layout.operator("outliner.bulk_add_collision_setting", text=physics_object[1]).physics_type = (
                    physics_object[0]
                )


def draw_bulk_add_collision_setting_menu(self: bpy.types.Menu, context: bpy.types.Context) -> None:
    layout = self.layout
    coll_of_menu: bpy.types.Collection | None = context.collection
    if layout and coll_of_menu:
        scene: GoblendScene = context.scene
        # this is much slower than a simple bpy.data.collections.get(bpy.context.scene.panel_props.collision_collection),
        # but it only includes collections of the current scene
        # it shouldn't matter too much with a low collection count
        all_collections_in_scene = scene.collection.children_recursive if scene else []
        collision_collection: bpy.types.Collection | None = None
        for coll in all_collections_in_scene:
            if coll.name == bpy.context.scene.panel_props.collision_collection:
                collision_collection = coll
                break
        all_child_collections = collision_collection.children_recursive if collision_collection else []
        # only show the menu if we right clicked a collision collection
        if coll_of_menu == collision_collection or coll_of_menu in all_child_collections:
            layout.separator()
            layout.menu("OUTLINER_MT_BulkAddCollisionSetting")
