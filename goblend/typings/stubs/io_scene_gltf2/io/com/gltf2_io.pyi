from gltf2_io_extensions import Extension
from typing import Any

class AnimationChannelTarget:
    """The index of the node and TRS property to target.

    The index of the node and TRS property that an animation channel targets.
    """

    extensions: dict[str, Extension]

    def __init__(self, extensions, extras, node, path) -> None: ...
    @staticmethod
    def from_dict(obj):  # -> AnimationChannelTarget:
        ...

    def to_dict(self):  # -> dict[Any, Any]:
        ...

class RealizedAnimationChannelTarget:
    extensions: dict[str, dict[str, Any]]

class AnimationChannel:
    """Targets an animation's sampler at a node's property."""

    target: AnimationChannelTarget

    def __init__(self, extensions, extras, sampler, target) -> None: ...
    @staticmethod
    def from_dict(obj):  # -> AnimationChannel:
        ...

    def to_dict(self):  # -> dict[Any, Any]:
        ...

class RealizedAnimationChannel:
    target: RealizedAnimationChannelTarget

class Animation:
    """A keyframe animation."""

    channels: list[AnimationChannel]
    name: str
    extensions: dict[str, Extension]

    def __init__(self, channels, extensions, extras, name, samplers) -> None: ...
    @staticmethod
    def from_dict(obj):  # -> Animation:
        ...

    def to_dict(self):  # -> dict[Any, Any]:
        ...

class RealizedAnimation:
    channels: list[RealizedAnimationChannel]
    name: str
    extensions: dict[str, dict[str, Any]]

class Material:
    """The material appearance of a primitive."""

    name: str
    extensions: dict[str, Extension]

    def __init__(
        self,
        alpha_cutoff,
        alpha_mode,
        double_sided,
        emissive_factor,
        emissive_texture,
        extensions,
        extras,
        name,
        normal_texture,
        occlusion_texture,
        pbr_metallic_roughness,
    ) -> None: ...
    @staticmethod
    def from_dict(obj):  # -> Material:
        ...

    def to_dict(self):  # -> dict[Any, Any]:
        ...

class MeshPrimitive:
    """Geometry to be rendered with the given material."""

    material: Material

    def __init__(self, attributes, extensions, extras, indices, material, mode, targets) -> None: ...
    @staticmethod
    def from_dict(obj):  # -> MeshPrimitive:
        ...

    def to_dict(self):  # -> dict[Any, Any]:
        ...

class Mesh:
    """A set of primitives to be rendered.  A node can contain one mesh.  A node's transform
    places the mesh in the scene.
    """

    primitives: list[MeshPrimitive]

    def __init__(self, extensions, extras, name, primitives, weights) -> None: ...
    @staticmethod
    def from_dict(obj):  # -> Mesh:
        ...

    def to_dict(self):  # -> dict[Any, Any]:
        ...

class Node:
    """A node in the node hierarchy.  When the node contains `skin`, all `mesh.primitives` must
    contain `JOINTS_0` and `WEIGHTS_0` attributes.  A node can have either a `matrix` or any
    combination of `translation`/`rotation`/`scale` (TRS) properties. TRS properties are
    converted to matrices and postmultiplied in the `T * R * S` order to compose the
    transformation matrix; first the scale is applied to the vertices, then the rotation, and
    then the translation. If none are provided, the transform is the identity. When a node is
    targeted for animation (referenced by an animation.channel.target), only TRS properties
    may be present; `matrix` will not be present.
    """

    children: list[Node]
    extensions: dict[str, Extension]
    mesh: Mesh | None
    name: str
    translation: list[float]

    def __init__(
        self,
        camera,
        children: list[Node],
        extensions: dict[str, Extension],
        extras,
        matrix,
        mesh,
        name,
        rotation,
        scale,
        skin,
        translation,
        weights,
    ) -> None: ...
    @staticmethod
    def from_dict(obj):  # -> Node:
        ...

    def to_dict(self):  # -> dict[Any, Any]:
        ...

class RealizedNode:
    children: list[int]

class Scene:
    """The root nodes of a scene."""

    nodes: list[Node]

    def __init__(self, extensions, extras, name, nodes) -> None: ...
    @staticmethod
    def from_dict(obj):  # -> Scene:
        ...

    def to_dict(self):  # -> dict[Any, Any]:
        ...

class RealizedScene:
    nodes: list[int]

class Gltf:
    """The root object for a glTF asset."""

    animations: list[RealizedAnimation]
    extensions: dict[str, Extension]
    nodes: list[RealizedNode]
    scenes: list[RealizedScene]

    def __init__(
        self,
        accessors,
        animations,
        asset,
        buffers,
        buffer_views,
        cameras,
        extensions,
        extensions_required,
        extensions_used,
        extras,
        images,
        materials,
        meshes,
        nodes,
        samplers,
        scene,
        scenes,
        skins,
        textures,
    ) -> None: ...
    @staticmethod
    def from_dict(obj):  # -> Gltf:
        ...

    def to_dict(self):  # -> dict[Any, Any]:
        ...
