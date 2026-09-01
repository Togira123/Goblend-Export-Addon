# RemoveMaterialSetting.py
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

from ...types.blender_types import OperatorReturnItems
from ...types.goblend_types import GoblendContext

from typing import cast

import bpy


class MaterialPanelContext(GoblendContext):
    material_setting_to_remove: bpy.types.Object


class SCENE_OT_RemoveMaterialSetting(bpy.types.Operator):
    bl_idname = "scene.remove_material_setting"
    bl_label = "Remove Material"
    bl_description = "Remove constraints for this material"

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        ctx = cast(MaterialPanelContext, context)
        mat = ctx.material_setting_to_remove
        for i in range(len(ctx.scene.material_panel_props)):
            if ctx.scene.material_panel_props[i].mat == mat:
                ctx.scene.material_panel_props.remove(i)
                break
        return {"FINISHED"}
