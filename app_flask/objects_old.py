from dataclasses import dataclass

@dataclass(slots=True)
class User:
    username: str
    password: bytes
    level: int = 99

@dataclass(slots=True)
class Share:
    id: str
    user: str
    sub_path: str
    anonymous_access: bool = False
