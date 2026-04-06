# RemoveObjectSetting.py
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


class SCENE_OT_RemoveObjectSetting(bpy.types.Operator):
    bl_idname = "scene.remove_object_setting"
    bl_label = "Remove Object Constraint"
    bl_description = "Remove constraints for an object"

    def execute(self, context):
        obj = context.object_setting_to_remove
        for i in range(len(context.scene.object_panel_props)):
            if context.scene.object_panel_props[i].obj == obj:
                context.scene.object_panel_props.remove(i)
                break
        return {"FINISHED"}
