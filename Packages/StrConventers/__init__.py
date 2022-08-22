from typing import *


def str2tuple(string: str, convert_items_to=None, default: any = None) -> Any:
    if isinstance(string, str):
        v = string.removeprefix('(').removesuffix(')').replace(',', ' ').split()
        if convert_items_to is not None:
            try:
                for index, item in enumerate(v):
                    v[index] = convert_items_to(item)

            except ValueError:
                return default

        return tuple(v)
    return default


def str2bool(string: str, default: Any = False) -> Any:
    if string == 'True':
        return True
    elif string == 'False':
        return False
    return default


def str2int(string: str, default: Any = 0) -> Any:
    if isinstance(string, int) or isinstance(string, float):
        return int(string)

    elif isinstance(string, str):
        string = string.strip()
        if is_negative := '-' == string[0]:
            string = string.replace('-', '', 1)
        if not string.isdecimal():
            return default
        if is_negative:
            string = '-' + string
        return int(string)
    return default


def str2float(string: str, default: Any = 0.) -> Any:
    if isinstance(string, int) or isinstance(string, float):
        return float(string)

    elif isinstance(string, str):
        string = string.strip()
        string = string.replace(',', '.')
        if is_negative := '-' == string[0]:
            string = string.replace('-', '', 1)
        for symbol in string:
            if symbol not in '0123456789.':
                return default
        if is_negative:
            string = '-' + string
        return float(string)
    return default
