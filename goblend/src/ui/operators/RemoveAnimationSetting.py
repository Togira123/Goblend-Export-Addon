# RemoveAnimationSetting.py
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

import bpy


from typing import cast


class AnimationPanelContext(GoblendContext):
    animation_to_remove: bpy.types.Action


class SCENE_OT_RemoveAnimationSetting(bpy.types.Operator):
    bl_idname = "scene.remove_animation_setting"
    bl_label = "Remove Animation Setting"
    bl_description = "Remove the animation setting for this animation"

    def execute(self, context: bpy.types.Context) -> set[OperatorReturnItems]:
        ctx = cast(AnimationPanelContext, context)
        animation = ctx.animation_to_remove
        for i in range(len(ctx.scene.animation_panel_props)):
            if ctx.scene.animation_panel_props[i].animation == animation:
                ctx.scene.animation_panel_props.remove(i)
                break
        return {"FINISHED"}
