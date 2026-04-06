# AddonPreferences.py
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
from ... import __package__ as base_package


class AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = base_package

    godot_file_path: bpy.props.StringProperty(
        name="Godot Executable", description="Choose the Godot Executable", subtype="FILE_PATH"
    )
    create_log_file: bpy.props.BoolProperty(
        name="Create Log File",
        description="If this is checked, each export will write its log to a log file created in the root of your project.",
        default=True,
    )

    def draw(self, context):
        self.layout.prop(self, "godot_file_path")
        self.layout.prop(self, "create_log_file")
