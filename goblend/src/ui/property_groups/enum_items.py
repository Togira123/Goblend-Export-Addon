# enum_items.py
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


shadow_cast_enum_items = [
    ("OFF", "Off", "Use SHADOW_CASTING_SETTING_OFF in Godot"),
    ("ON", "On", "Use SHADOW_CASTING_SETTING_ON in Godot"),
    ("DOUBLE_SIDED", "Double Sided", "Use SHADOW_CASTING_SETTING_DOUBLE_SIDED in Godot"),
    ("SHADOWS_ONLY", "Shadows Only", "Use SHADOW_CASTING_SETTING_SHADOWS_ONLY in Godot"),
]

transparency_enum_items = [
    ("ALPHA", "Alpha", "Use TRANSPARENCY_ALPHA mode in Godot"),
    ("SCISSOR", "Alpha Scissor", "Use TRANSPARENCY_ALPHA_SCISSOR mode in Godot"),
    ("HASH", "Alpha Hash", "Use TRANSPARENCY_ALPHA_HASH mode in Godot"),
    ("DEPTH_PRE_PASS", "Depth Pre-Pass", "Use TRANSPARENCY_ALPHA_DEPTH_PRE_PASS in Godot"),
]

culling_enum_items = [
    ("DISABLED", "Disabled", "Use Cull Mode Disabled in Godot"),
    ("BACK", "Back", "Use Cull Mode Back in Godot"),
    ("FRONT", "Front", "Use Cull Mode Front in Godot"),
]

physics_objects = [
    ("STATIC_BODY", "StaticBody3D", "Use StaticBody3D in Godot"),
    ("CHARACTER_BODY", "CharacterBody3D", "Use CharacterBody3D in Godot"),
    ("RIGID_BODY", "RigidBody3D", "Use RigidBody3D in Godot"),
    ("ANIMATABLE_BODY", "AnimatableBody3D", "Use AnimatableBody3D in Godot"),
    ("AREA", "Area3D", "Use Area3D in Godot"),
    ("NODE", "Node3D (No Physics Object)", "Use Node3D in Godot"),
]
