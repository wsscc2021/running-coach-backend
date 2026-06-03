_collecting: bool = False


def is_collecting() -> bool:
    return _collecting


def set_collecting(value: bool) -> None:
    global _collecting
    _collecting = value
