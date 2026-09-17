"""Domain models for the contact book."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Contact:
    """A stored contact."""

    id: int
    name: str
    phone: str = ""
    email: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Contact":
        return cls(
            id=int(data["id"]),
            name=str(data["name"]),
            phone=str(data.get("phone", "")),
            email=str(data.get("email", "")),
        )
