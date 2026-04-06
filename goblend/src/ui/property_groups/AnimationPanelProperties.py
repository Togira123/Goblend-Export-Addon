# AnimationPanelProperties.py
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


def is_not_action_picked_already(self, action):
    if action.library != None:
        return False
    scene = bpy.context.scene
    for item in scene.animation_panel_props:
        if item.animation == action:
            return False
    return True


class AnimationPanelProperties(bpy.types.PropertyGroup):
    open: bpy.props.BoolProperty(default=True)
    animation: bpy.props.PointerProperty(name="Animation", type=bpy.types.Action, poll=is_not_action_picked_already)
    autoplay: bpy.props.BoolProperty(
        name="Autoplay", description="Mark Animation to play automatically on load", default=False
    )
    loop: bpy.props.BoolProperty(name="Loop", description="Make the animation loop", default=False)
