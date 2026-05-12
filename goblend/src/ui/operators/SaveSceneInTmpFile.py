# SaveSceneInTmpFile.py
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

from .ExportToGodot import get_export_paths
from ...config import get_config
from ...export.handle_materials import write_tmp_file


class SCENE_OT_SaveSceneInTmpFile(bpy.types.Operator):
    bl_idname = "scene.save_scene_in_tmp_file"
    bl_label = "Save Scene in Temporary File"
    bl_description = "Saves the path of this scene in the .tmp.goblend file."

    def execute(self, context):
        paths = get_export_paths(get_config(), props=context.scene.panel_props)

        write_tmp_file(paths)
        return {"FINISHED"}
