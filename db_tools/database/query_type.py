from enum import Enum, auto

class QueryType(Enum):
    DQL = auto()
    DML = auto()
    DDL = auto()
    DCL = auto()

    @property
    def returns_data(self: "QueryType") -> bool:
        return self == QueryType.DQL
