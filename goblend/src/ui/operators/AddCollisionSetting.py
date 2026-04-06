# AddCollisionSetting.py
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


class SCENE_OT_AddCollisionSetting(bpy.types.Operator):
    bl_idname = "scene.add_collision_setting"
    bl_label = "Add Collision Setting"
    bl_description = "Customize collision settings for different collision collections"

    def execute(self, context):
        context.scene.collision_panel_props.add()
        return {"FINISHED"}
