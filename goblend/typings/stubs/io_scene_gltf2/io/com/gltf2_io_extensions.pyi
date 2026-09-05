from typing import Any, Dict, List, TypedDict

class Extension:
    """Container for extensions. Allows to specify requiredness"""

    extension = ...
    def __init__(self, name: str, extension: TypedDict, required: bool = ...) -> None: ...

class ChildOfRootExtension(Extension):
    """Container object for extensions that should be appended to the root extensions"""

    def __init__(self, path: List[str], name: str, extension: Dict[str, Any], required: bool = ...) -> None:
        """
        Wrap a local extension entity into an object that will later be inserted into a root extension and converted
        to a reference.
        :param path: The path of the extension object in the root extension. E.g. ['lights'] for
        KHR_lights_punctual. Must be a path to a list in the extensions dict.
        :param extension: The data that should be placed into the extension list
        """
        ...
