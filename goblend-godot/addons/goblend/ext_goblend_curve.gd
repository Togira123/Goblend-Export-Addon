# ext_goblend_curve.gd
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
class_name GLTFDocumentExtensionEXTGoblendCurve extends GLTFDocumentExtension

var ext_name := "EXT_goblend_curve"

func _import_preflight(_state: GLTFState, extensions: PackedStringArray) -> Error:
	if extensions.has(ext_name):
		return OK
	return ERR_SKIP

func _get_supported_extensions() -> PackedStringArray:
	return PackedStringArray([ext_name])

func _parse_node_extensions(_state: GLTFState, gltf_node: GLTFNode, extensions: Dictionary) -> Error:
	if not extensions.has(ext_name):
		return OK
	var ext: Dictionary = extensions[ext_name]
	gltf_node.set_additional_data(ext_name, ext)
	return OK

func _import_node(_state: GLTFState, gltf_node: GLTFNode, _json: Dictionary, node: Node) -> Error:
	var ext = gltf_node.get_additional_data(ext_name)
	if ext == null:
		return OK
	if not ext.has("curves"):
		return ERR_INVALID_DATA

	var curves: Array = ext["curves"]
	if curves.size() <= 1:
		var old_node := node
		var path3d := Path3D.new()
		path3d.transform = node.transform
		if curves.size() == 1:
			var curve := create_curve_3d(curves[0])
			path3d.curve = curve
		node.replace_by(path3d)
		path3d.name = old_node.name
		old_node.free()
	else:
		for curve_data in curves:
			var path3d := Path3D.new()
			var curve := create_curve_3d(curve_data)
			path3d.curve = curve
			node.add_child(path3d)
			path3d.owner = node.owner
			path3d.name = node.name
	return OK

func arr_to_vec(arr: Array) -> Vector3:
	return Vector3(arr[0], arr[1], arr[2])

func create_curve_3d(data: Dictionary) -> Curve3D:
	var curve := Curve3D.new()
	curve.closed = data["closed"]
	var points: Array = data["points"]
	for point in points:
		var position := arr_to_vec(point["coord"])
		curve.add_point(position, arr_to_vec(point["in_coord"]) - position, arr_to_vec(point["out_coord"]) - position)
		curve.set_point_tilt(curve.point_count - 1, point["tilt"])
	return curve
