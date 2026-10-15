# Классы предметной области «Детективное агентство»
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from exceptions import (
    InvalidReliabilityError,
    InvalidSuspicionLevelError,
    SuspectAlreadyClearedError,
)


# Перечисления: фиксированные варианты
class CaseStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    SUSPENDED = "suspended"
    CLOSED = "closed"
    ARCHIVED = "archived"


class CasePriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceType(Enum):
    FINGERPRINT = "fingerprint"
    DNA = "dna"
    PHOTO = "photo"
    DOCUMENT = "document"
    WEAPON = "weapon"
    DIGITAL = "digital"


class Specialization(Enum):
    DETECTIVE = "detective"
    FORENSIC = "forensic"
    CYBER = "cyber"
    ANALYST = "analyst"


# Общие проверки входных данных, чтобы не повторять их в каждом классе
def check_text(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field}: ожидалась строка, получено {value!r}")
    if not value.strip():
        raise ValueError(f"{field}: значение не может быть пустым")
    return value.strip()


def check_int(value: Any, field: str) -> int:
    # bool тоже считается int в Python, поэтому исключаем его отдельно
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field}: ожидалось целое число, получено {value!r}")
    return value


def check_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field}: ожидалось число, получено {value!r}")
    return float(value)


# Абстрактный родитель всех сущностей: id, дата создания, to_dict/from_dict
class BaseEntity(ABC):

    def __init__(self, entity_id: UUID | None = None,
                 created_at: datetime | None = None) -> None:
        # новый объект получает новый UUID, загруженный из файла сохраняет свой
        self._id = entity_id if entity_id is not None else uuid4()
        self._created_at = (created_at if created_at is not None
                            else datetime.now())

    # только чтение: id нельзя подменить снаружи
    @property
    def id(self) -> UUID:
        return self._id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    # общая часть словаря, наследники дописывают в неё свои поля
    def _base_dict(self) -> dict[str, Any]:
        return {
            "id": str(self._id),
            "created_at": self._created_at.isoformat(),
        }

    # каждый наследник обязан уметь превращаться в словарь
    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        pass

    # и восстанавливаться из словаря (вызывается у класса, объекта ещё нет)
    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseEntity":
        pass


# Человек: общий родитель детектива, подозреваемого и свидетеля.
# Остаётся абстрактным: to_dict, from_dict и get_role реализуют наследники.
class Person(BaseEntity):

    def __init__(self, name: str, contact: str,
                 entity_id: UUID | None = None,
                 created_at: datetime | None = None) -> None:
        super().__init__(entity_id, created_at)
        # присваиваем через свойства, чтобы сработала проверка
        self.name = name
        self.contact = contact

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = check_text(value, "Имя")

    @property
    def contact(self) -> str:
        return self._contact

    @contact.setter
    def contact(self, value: str) -> None:
        self._contact = check_text(value, "Контакт")

    # роль человека в деле: каждый наследник отвечает по-своему
    @abstractmethod
    def get_role(self) -> str:
        pass

    def _base_dict(self) -> dict[str, Any]:
        data = super()._base_dict()
        # роль по имени класса: detective / suspect / witness
        data["role"] = type(self).__name__.lower()
        data["name"] = self._name
        data["contact"] = self._contact
        return data

    def __str__(self) -> str:
        return f"{self.get_role()} {self._name}"


class Detective(Person):

    def __init__(self, name: str, contact: str,
                 specialization: Specialization, rank: str,
                 solved_cases: int = 0,
                 entity_id: UUID | None = None,
                 created_at: datetime | None = None) -> None:
        super().__init__(name, contact, entity_id, created_at)
        if not isinstance(specialization, Specialization):
            raise TypeError("Специализация должна быть Specialization")
        self._specialization = specialization
        self._rank = check_text(rank, "Звание")
        self._solved_cases = check_int(solved_cases, "Раскрытые дела")
        if self._solved_cases < 0:
            raise ValueError("Число раскрытых дел не может быть меньше 0")

    @property
    def specialization(self) -> Specialization:
        return self._specialization

    @property
    def rank(self) -> str:
        return self._rank

    @property
    def solved_cases(self) -> int:
        return self._solved_cases

    def get_role(self) -> str:
        return "Детектив"

    # детектив берёт дело: становится его ведущим
    def take_case(self, case: "Case") -> None:
        case.lead_detective = self

    # закрыть дело может только его ведущий детектив
    def close_case(self, case: "Case") -> None:
        if case.lead_detective is None or case.lead_detective.id != self.id:
            raise ValueError(
                f"{self.name} не ведёт дело «{case.title}», закрыть нельзя"
            )
        case.close()
        self._solved_cases += 1

    def to_dict(self) -> dict[str, Any]:
        data = self._base_dict()
        data["specialization"] = self._specialization.value
        data["rank"] = self._rank
        data["solved_cases"] = self._solved_cases
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Detective":
        return cls(
            data["name"],
            data["contact"],
            Specialization(data["specialization"]),
            data["rank"],
            data["solved_cases"],
            UUID(data["id"]),
            datetime.fromisoformat(data["created_at"]),
        )


class Suspect(Person):

    def __init__(self, name: str, contact: str, alibi: str,
                 suspicion_level: int = 0, cleared: bool = False,
                 entity_id: UUID | None = None,
                 created_at: datetime | None = None) -> None:
        super().__init__(name, contact, entity_id, created_at)
        self.alibi = alibi
        self.suspicion_level = suspicion_level
        self._cleared = bool(cleared)

    @property
    def alibi(self) -> str:
        return self._alibi

    @alibi.setter
    def alibi(self, value: str) -> None:
        self._alibi = check_text(value, "Алиби")

    @property
    def suspicion_level(self) -> int:
        return self._suspicion_level

    # уровень подозрения проверяется при любом изменении: только 0–100
    @suspicion_level.setter
    def suspicion_level(self, value: int) -> None:
        value = check_int(value, "Уровень подозрения")
        if not 0 <= value <= 100:
            raise InvalidSuspicionLevelError(value)
        self._suspicion_level = value

    @property
    def cleared(self) -> bool:
        return self._cleared

    def get_role(self) -> str:
        return "Подозреваемый"

    def raise_suspicion(self, amount: int) -> None:
        if self._cleared:
            raise SuspectAlreadyClearedError(self.name)
        self.suspicion_level = self._suspicion_level + check_int(
            amount, "Прирост подозрения")

    def clear_suspect(self) -> None:
        if self._cleared:
            raise SuspectAlreadyClearedError(self.name)
        self._cleared = True
        self._suspicion_level = 0

    def to_dict(self) -> dict[str, Any]:
        data = self._base_dict()
        data["alibi"] = self._alibi
        data["suspicion_level"] = self._suspicion_level
        data["cleared"] = self._cleared
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Suspect":
        return cls(
            data["name"],
            data["contact"],
            data["alibi"],
            data["suspicion_level"],
            data["cleared"],
            UUID(data["id"]),
            datetime.fromisoformat(data["created_at"]),
        )


class Witness(Person):

    def __init__(self, name: str, contact: str, testimony: str,
                 reliability: int = 5,
                 entity_id: UUID | None = None,
                 created_at: datetime | None = None) -> None:
        super().__init__(name, contact, entity_id, created_at)
        self.testimony = testimony
        self.reliability = reliability

    @property
    def testimony(self) -> str:
        return self._testimony

    @testimony.setter
    def testimony(self, value: str) -> None:
        self._testimony = check_text(value, "Показания")

    @property
    def reliability(self) -> int:
        return self._reliability

    # надёжность свидетеля по шкале 1–10
    @reliability.setter
    def reliability(self, value: int) -> None:
        value = check_int(value, "Надёжность")
        if not 1 <= value <= 10:
            raise InvalidReliabilityError(value)
        self._reliability = value

    def get_role(self) -> str:
        return "Свидетель"

    def to_dict(self) -> dict[str, Any]:
        data = self._base_dict()
        data["testimony"] = self._testimony
        data["reliability"] = self._reliability
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Witness":
        return cls(
            data["name"],
            data["contact"],
            data["testimony"],
            data["reliability"],
            UUID(data["id"]),
            datetime.fromisoformat(data["created_at"]),
        )