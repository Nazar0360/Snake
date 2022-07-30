from typing import *


def str2tuple(string: str, convert_items_to=None, default=None) -> Any:
    if isinstance(string, str):
        v = string.removeprefix('(').removesuffix(')').replace(',', ' ').split()
        if convert_items_to is not None:
            try:
                for index, item in enumerate(v):
                    v[index] = convert_items_to(item)

            except ValueError:
                return default

        return tuple(v)
    else:
        return default


def str2bool(string: str, default=False):
    if string == 'True':
        return True
    elif string == 'False':
        return False
    else:
        return default


def str2int(string: str, default: Any = 0):
    if isinstance(string, int) or isinstance(string, float):
        return int(string)

    elif isinstance(string, str):
        try:
            return int(string)
        except ValueError:
            return default
    return default
