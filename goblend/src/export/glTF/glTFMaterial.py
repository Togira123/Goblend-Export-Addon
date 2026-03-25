import bpy


class glTFMaterialShaderUniform(bpy.types.PropertyGroup):
    var_name: bpy.props.StringProperty()
    uniform_data: bpy.props.StringProperty()


class glTFMaterial(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()

    transparency_mode: bpy.props.StringProperty()
    transparency_alpha_scissor_threshold: bpy.props.FloatProperty()
    cull_mode: bpy.props.StringProperty()

    shader_code: bpy.props.StringProperty(default="")
    shader_uniforms: bpy.props.CollectionProperty(type=glTFMaterialShaderUniform)
