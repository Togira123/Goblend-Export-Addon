# ext_goblend_convert_importer_mesh.gd
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
class_name GLTFDocumentExtensionEXTGoblendConvertImporterMesh extends GLTFDocumentExtensionConvertImporterMesh

var ext_name := "EXT_goblend_general"

# create this override simply because using GLTFDocumentExtensionConvertImporterMesh directly would
# mess with glTF files that are imported without Goblend, this way it is only applied when Goblend was used
func _import_preflight(state: GLTFState, extensions: PackedStringArray) -> Error:
	if extensions.has(ext_name):
		return OK
	return ERR_SKIP
