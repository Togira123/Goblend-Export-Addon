# ext_goblend_animation.gd
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


@tool
class_name GLTFDocumentExtensionEXTGoblendAnimation extends GLTFDocumentExtension

var ext_name := "EXT_goblend_animation"

func _import_preflight(_state: GLTFState, extensions: PackedStringArray) -> Error:
	if extensions.has(ext_name):
		return OK
	return ERR_SKIP

func _get_supported_extensions() -> PackedStringArray:
	return PackedStringArray([ext_name])

func _import_post(state: GLTFState, root: Node) -> Error:
	var anim_player = find_anim_player(root)
	if anim_player == null:
		return OK
	if not state.json.has("animations"):
		return OK
	for animation in state.json["animations"]:
		if not animation.has("extensions"):
			continue
		if not animation["extensions"].has(ext_name):
			continue
		var data: Dictionary = animation["extensions"][ext_name]
		if data.has("autoplay") and data["autoplay"]:
			# root.name is library name
			anim_player.autoplay = root.name + "/" + animation["name"]
		if data.has("loop") and data["loop"]:
			var anim: Animation = anim_player.get_animation(animation["name"])
			anim.loop = true

	return OK

func find_anim_player(root: Node) -> AnimationPlayer:
	if root is AnimationPlayer:
		return root
	for child in root.get_children():
		var val := find_anim_player(child)
		if val:
			return val
	return null
