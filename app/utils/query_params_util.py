from typing import Optional, Union, Any


def parse_optional_string(value: Optional[Union[str, Any]]) -> Optional[str]:

    if value == "" or value is None:
        return None
    return value


def parse_optional_int(value: Optional[Union[str, int, Any]]) -> Optional[int]:
    if value == "" or value is None:
        return None
    
    if isinstance(value, int):
        return value
    
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    
    return None


def parse_optional_float(value: Optional[Union[str, float, Any]]) -> Optional[float]:
    if value == "" or value is None:
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    
    return None


def parse_optional_bool(value: Optional[Union[str, bool, Any]]) -> Optional[bool]:
    if value == "" or value is None:
        return None
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        value_lower = value.lower()
        if value_lower in ("true", "1", "yes", "y"):
            return True
        elif value_lower in ("false", "0", "no", "n"):
            return False
    
    return None