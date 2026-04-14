"""
Weight class mapper — maps OS/2 usWeightClass to human-readable names.
"""

WEIGHT_MAP = {
    100: "Thin",
    200: "ExtraLight",
    250: "UltraLight",
    300: "Light",
    350: "SemiLight",
    380: "DemiLight",
    400: "Regular",
    450: "Medium",
    500: "Medium",
    600: "SemiBold",
    700: "Bold",
    800: "ExtraBold",
    850: "UltraBold",
    900: "Black",
    950: "UltraBlack",
}


def weight_class_to_name(weight_class: int) -> str:
    """
    Map an OS/2 weight class number to a human-readable name.

    Args:
        weight_class: Integer from 100-900 (OS/2 usWeightClass).

    Returns:
        Human-readable weight name.
    """
    return WEIGHT_MAP.get(weight_class, f"Weight{weight_class}")


def weight_name_to_class(weight_name: str) -> int:
    """
    Map a human-readable weight name to an OS/2 weight class number.

    Args:
        weight_name: Weight name (case-insensitive).

    Returns:
        Integer weight class.
    """
    name = weight_name.lower().replace(" ", "").replace("-", "")
    reverse_map = {v.lower().replace(" ", ""): k for k, v in WEIGHT_MAP.items()}
    return reverse_map.get(name, 400)
