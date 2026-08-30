# property_types.py
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


from typing import TYPE_CHECKING, Any, Callable, ParamSpec, TypeVar

import bpy
import collections.abc as abc

# this is needed to not get type errors when accessing these properties
# At runtime it will just be bpy.types.Scene
if TYPE_CHECKING:

    # these are needed because the blender props return _PropertyDeferred

    P = ParamSpec("P")
    T = TypeVar("T")

    def correct_ret_type(fn: Callable[P, Any], t: type[T]) -> Callable[P, T]: ...

    BoolProp = correct_ret_type(bpy.props.BoolProperty, bool)
    IntProp = correct_ret_type(bpy.props.IntProperty, int)
    FloatProp = correct_ret_type(bpy.props.FloatProperty, float)
    StringProp = correct_ret_type(bpy.props.StringProperty, str)
    IntVectorProp = correct_ret_type(bpy.props.IntVectorProperty, list[int])
    FloatVectorProp = correct_ret_type(bpy.props.FloatVectorProperty, list[float])
    EnumProp = correct_ret_type(bpy.props.EnumProperty, str)

    # the following two are copied from the fake module definitions because we need the generic type for the return type

    # left out options and override parameters since they rely on internal types and we don't really need them

    T1 = TypeVar("T1", bound=bpy.types.PropertyGroup)

    def CollectionProp(
        *,
        type: type[T1],
        name: str | None = "",
        description: str | None = "",
        translation_context: str | None = "*",
        tags: set[str] | None = set(),
    ) -> bpy.types.bpy_prop_collection_idprop[T1]: ...

    T2 = TypeVar("T2", bound=bpy.types.bpy_struct)
    T3 = TypeVar("T3", bound=bpy.types.ID)
    T4 = TypeVar("T4", bound=bpy.types.PropertyGroup | bpy.types.ID)

    def PointerProp(
        *,
        type: type[T4],
        name: str | None = "",
        description: str | None = "",
        translation_context: str | None = "*",
        tags: set[str] | None = set(),
        poll: abc.Callable[[T2, T3], bool] | None = None,
        update: abc.Callable[[T2, bpy.types.Context], None] | None = None,
    ) -> T4: ...

else:
    BoolProp = bpy.props.BoolProperty
    IntProp = bpy.props.IntProperty
    FloatProp = bpy.props.FloatProperty
    StringProp = bpy.props.StringProperty
    IntVectorProp = bpy.props.IntVectorProperty
    FloatVectorProp = bpy.props.FloatVectorProperty
    EnumProp = bpy.props.EnumProperty
    CollectionProp = bpy.props.CollectionProperty
    PointerProp = bpy.props.PointerProperty

U = TypeVar("U", bound=bpy.types.bpy_struct)


# we add this function as a decorator to all property group definitions
# that way we can use foo = Prop(...) instead of foo: Prop(...)
# which will allow us to use the correct types together with the definitions above
def typed_prop_group(cls: type[U]) -> type[U]:
    for name, value in list(vars(cls).items()):
        if isinstance(value, bpy.props._PropertyDeferred):
            cls.__annotations__[name] = value
            delattr(cls, name)
    return cls
