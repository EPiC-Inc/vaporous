from dataclasses import dataclass

@dataclass(slots=True)
class User:
    username: str
    password: bytes

@dataclass(slots=True)
class Share:
    user: str
    sub_path: str
