@tool
class_name GLTFDocumentExtensionEXTGoblendMaterial extends GLTFDocumentExtension

var ext_name := "EXT_goblend_material"

func _import_preflight(_state: GLTFState, extensions: PackedStringArray) -> Error:
	if extensions.has(ext_name):
		return OK
	return ERR_SKIP

func _get_supported_extensions() -> PackedStringArray:
	return PackedStringArray([ext_name])

func _import_node(state: GLTFState, gltf_node: GLTFNode, _json: Dictionary, node: Node) -> Error:
	if node is ImporterMeshInstance3D:
		var mesh: ImporterMesh = node.mesh
		if state.json.has("materials"):
			var gltf_materials: Array = state.json["materials"]
			var gltf_material_count := gltf_materials.size()
			var surface_count := mesh.get_surface_count()
			for i in surface_count:
				var mat := mesh.get_surface_material(i)
				if mat.resource_name == "":
					continue
				# find corresponding gltf material
				var gltf_mat: Dictionary = {}
				var mat_index := 0
				while mat_index < gltf_material_count:
					var gltf_material: Dictionary = gltf_materials[mat_index]
					var gltf_material_name = gltf_material["name"] if gltf_material.has("name") else ("material_%s" % str(mat_index))
					if mat.resource_name == gltf_material_name:
						gltf_mat = gltf_material
						break
					mat_index += 1
				if gltf_mat.is_empty():
					Goblend.log_msg("Failed to find material with name " + mat.resource_name + " in glTF data", "ERROR")
					return ERR_INVALID_DATA
				
				if not gltf_mat.has("extensions") or not gltf_mat["extensions"].has(ext_name):
					continue
				var ext_data: Dictionary = gltf_mat["extensions"][ext_name]
				# check whether the material should be a shader
				if ext_data.has("shader_code") and ext_data["shader_code"] != "":
					var shader_mat := ShaderMaterial.new()
					shader_mat.resource_name = mat.resource_name
					var shader := Shader.new()
					shader.code = ext_data["shader_code"]
					if ext_data.has("shader_uniforms"):
						for uniform in ext_data["shader_uniforms"]:
							var var_name: String = uniform["var_name"]
							var uniform_data: String = uniform["uniform_data"]
							# we are assuming here that uniform_data will always be a path to a resource
							# this is the case right now, but may change in the future
							shader_mat.set_shader_parameter(var_name, load(uniform_data))
					shader_mat.shader = shader
					mesh.set_surface_material(i, shader_mat)
				else:
					# not a shader
					if ext_data.has("transparency_mode") and mat.transparency != BaseMaterial3D.Transparency.TRANSPARENCY_DISABLED:
						match ext_data["transparency_mode"]:
							"ALPHA":
								mat.transparency = BaseMaterial3D.Transparency.TRANSPARENCY_ALPHA
							"SCISSOR":
								mat.transparency = BaseMaterial3D.Transparency.TRANSPARENCY_ALPHA_SCISSOR
								if ext_data.has("transparency_alpha_scissor_threshold"):
									mat.alpha_scissor_threshold = ext_data["transparency_alpha_scissor_threshold"]
							"HASH":
								mat.transparency = BaseMaterial3D.Transparency.TRANSPARENCY_ALPHA_HASH
							"DEPTH_PRE_PASS":
								mat.transparency = BaseMaterial3D.Transparency.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS
							_:
								return ERR_INVALID_DATA
					if ext_data.has("cull_mode"):
						match ext_data["cull_mode"]:
							"DISABLED":
								mat.cull_mode = BaseMaterial3D.CullMode.CULL_DISABLED
							"BACK":
								mat.cull_mode = BaseMaterial3D.CullMode.CULL_BACK
							"FRONT":
								mat.cull_mode = BaseMaterial3D.CullMode.CULL_FRONT
							_:
								return ERR_INVALID_DATA
					mesh.set_surface_material(i, mat)
	return OK
