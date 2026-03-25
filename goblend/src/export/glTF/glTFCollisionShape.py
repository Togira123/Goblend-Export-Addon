import bpy


class glTFCollisionShape(bpy.types.PropertyGroup):
    type: bpy.props.StringProperty()
    parent_name: bpy.props.StringProperty()
    object: bpy.props.PointerProperty(type=bpy.types.Object)

    # for box
    dimensions: bpy.props.FloatVectorProperty(size=3)

    # for cylinder
    height: bpy.props.FloatProperty()

    # for cylinder and sphere
    radius: bpy.props.FloatProperty()
