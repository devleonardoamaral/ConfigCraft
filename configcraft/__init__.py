from typing import Final

VERSION: Final[str] = "0.0.1"

from .configmanager import ConfigCraft
from .configblueprint import ConfigBlueprint

from . import configmanager
from . import configblueprint
from . import configerrors
from . import configutils
