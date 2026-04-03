@tool
class_name GLTFDocumentExtensionEXTGoblendObject extends GLTFDocumentExtension

var ext_name := "EXT_goblend_object"

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

# this can be used if the Godot bug is fixed that ignores cast_shadow on ImporterMeshInstance3D

#func _import_node(state: GLTFState, gltf_node: GLTFNode, _json: Dictionary, node: Node) -> Error:
	#var ext = gltf_node.get_additional_data(ext_name)
	#if ext == null:
		#return OK
	#var setting: GeometryInstance3D.ShadowCastingSetting
	#var shadow_cast_mode: String = ext["shadow_cast_mode"]
	#match shadow_cast_mode:
		#"OFF":
			#setting = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		#"ON":
			#setting = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		#"DOUBLE_SIDED":
			#setting = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
		#"SHADOWS_ONLY":
			#setting = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
		#_:
			#Goblend.log_msg("Unknown shadow cast mode found: " + shadow_cast_mode, "WARNING")
	#
	#node.cast_shadow = setting
	#return OK

func _import_post(state: GLTFState, root: Node) -> Error:
	iterate_nodes(state, root)
	return OK

func iterate_nodes(state: GLTFState, node: Node) -> void:
	var nodes := state.get_nodes()
	var gltf_node: GLTFNode = null
	for n in nodes:
		if n.original_name.validate_node_name() == node.name:
			gltf_node = n
			break
	if gltf_node:
		var ext = gltf_node.get_additional_data(ext_name)
		if ext != null:
			var setting: GeometryInstance3D.ShadowCastingSetting
			var shadow_cast_mode: String = ext["shadow_cast_mode"]
			match shadow_cast_mode:
				"OFF":
					setting = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				"ON":
					setting = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
				"DOUBLE_SIDED":
					setting = GeometryInstance3D.SHADOW_CASTING_SETTING_DOUBLE_SIDED
				"SHADOWS_ONLY":
					setting = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
				_:
					Goblend.log_msg("Unknown shadow cast mode found: " + shadow_cast_mode, "WARNING")
			node.cast_shadow = setting
	for child in node.get_children():
		iterate_nodes(state, child)
