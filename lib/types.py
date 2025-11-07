from typing import Any


class Struct(dict):
    def __init__(self: "Struct", *args, **kwargs):
        super().__init__(*args, **kwargs)

        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = Struct(value)
            if isinstance(value, list):
                self[key] = [
                    Struct(item) if isinstance(item, dict) else item for item in value
                ]

    def __getattr__(self: "Struct", key: Any):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"{type(self).__name__} has no attribute {key}!")

    def __setattr__(self: "Struct", key: Any, value: Any):
        if isinstance(value, dict):
            value = Struct(value)
        self[key] = value
