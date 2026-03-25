@tool
class_name GLTFDocumentExtensionEXTGoblendLight extends GLTFDocumentExtension

var ext_name := "EXT_goblend_light"

func _import_preflight(_state: GLTFState, extensions: PackedStringArray) -> Error:
	if extensions.has(ext_name):
		return OK
	return ERR_SKIP

func _get_supported_extensions() -> PackedStringArray:
	return PackedStringArray([ext_name])

func _parse_node_extensions(state: GLTFState, gltf_node: GLTFNode, extensions: Dictionary) -> Error:
	if not extensions.has(ext_name):
		return OK
	var ext: Dictionary = extensions[ext_name]
	gltf_node.set_additional_data(ext_name, ext)
	return OK

func _import_node(state: GLTFState, gltf_node: GLTFNode, _json: Dictionary, node: Node) -> Error:
	var ext = gltf_node.get_additional_data(ext_name)
	if ext == null:
		return OK
	if not node is Light3D:
		return ERR_INVALID_DATA
	
	if ext.has("light_color"):
		# we have to cast this one
		ext["light_color"] = Color(ext["light_color"][0], ext["light_color"][1], ext["light_color"][2])

	var props := PackedStringArray([
		"omni_range",
		"omni_attenuation",
		"omni_shadow_mode",
		"spot_range",
		"spot_attenuation",
		"spot_angle",
		"spot_angle_attenuation",
		"light_color",
		"light_energy",
		"light_indirect_energy",
		"light_volumetric_fog_energy",
		"light_angular_distance",
		"light_size",
		"light_negative",
		"light_specular",
		"light_bake_mode",
		"light_cull_mask",
        "shadow_enabled"
	])
	for prop in props:
		try_set_prop_on_light(node, ext, prop)

	return OK

func try_set_prop_on_light(node: Light3D, ext: Dictionary, prop: String) -> void:
	if not ext.has(prop):
		return
	if prop.begins_with("omni_"):
		if node is OmniLight3D:
			node[prop] = ext[prop]
	elif prop.begins_with("spot_"):
		if node is SpotLight3D:
			node[prop] = ext[prop]
	else:
		node[prop] = ext[prop]
