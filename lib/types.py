from typing import Any


class Struct(dict):
    """
    A dictionary-like object that allows accessing keys as attributes.
    """

    def __init__(self: "Struct", *args, **kwargs):
        """
        Initializes a new Struct object.
        """
        super().__init__(*args, **kwargs)

        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = Struct(value)
            if isinstance(value, list):
                self[key] = [
                    Struct(item) if isinstance(item, dict) else item for item in value
                ]

    def __getattr__(self: "Struct", key: Any):
        """
        Retrieves an item from the Struct as an attribute.
        """
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"{type(self).__name__} has no attribute {key}!")

    def __setattr__(self: "Struct", key: Any, value: Any):
        """
        Sets an item in the Struct as an attribute.
        """
        if isinstance(value, dict):
            value = Struct(value)
        self[key] = value
