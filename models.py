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


# Место: адрес и координаты. Своего id не имеет, поэтому не BaseEntity
class Location:

    def __init__(self, address: str, place_type: str,
                 latitude: float, longitude: float) -> None:
        self._address = check_text(address, "Адрес")
        self._place_type = check_text(place_type, "Тип места")
        self._latitude = check_number(latitude, "Широта")
        self._longitude = check_number(longitude, "Долгота")
        if not -90 <= self._latitude <= 90:
            raise ValueError("Широта должна быть от -90 до 90")
        if not -180 <= self._longitude <= 180:
            raise ValueError("Долгота должна быть от -180 до 180")

    @property
    def address(self) -> str:
        return self._address

    @property
    def place_type(self) -> str:
        return self._place_type

    @property
    def latitude(self) -> float:
        return self._latitude

    @property
    def longitude(self) -> float:
        return self._longitude

    def to_dict(self) -> dict[str, Any]:
        return {
            "address": self._address,
            "place_type": self._place_type,
            "latitude": self._latitude,
            "longitude": self._longitude,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Location":
        return cls(data["address"], data["place_type"],
                   data["latitude"], data["longitude"])

    def __str__(self) -> str:
        return f"{self._place_type}, {self._address}"


# Улика: абстрактный класс, конкретные виды описывают себя по-своему
class Evidence(BaseEntity):

    def __init__(self, evidence_type: EvidenceType, description: str,
                 found_at: Location,
                 entity_id: UUID | None = None,
                 created_at: datetime | None = None) -> None:
        super().__init__(entity_id, created_at)
        if not isinstance(evidence_type, EvidenceType):
            raise TypeError("Тип улики должен быть EvidenceType")
        if not isinstance(found_at, Location):
            raise TypeError("Место находки должно быть Location")
        self._evidence_type = evidence_type
        self._description = check_text(description, "Описание улики")
        self._found_at = found_at

    @property
    def evidence_type(self) -> EvidenceType:
        return self._evidence_type

    @property
    def description(self) -> str:
        return self._description

    @property
    def found_at(self) -> Location:
        return self._found_at

    # полиморфизм: у каждой улики своя сводка
    @abstractmethod
    def get_summary(self) -> str:
        pass

    def _base_dict(self) -> dict[str, Any]:
        data = super()._base_dict()
        data["evidence_type"] = self._evidence_type.value
        data["description"] = self._description
        data["found_at"] = self._found_at.to_dict()
        return data

    # по полю kind выбираем, объект какого класса создать
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Evidence":
        kinds: dict[str, type[Evidence]] = {
            "physical": PhysicalEvidence,
            "digital": DigitalEvidence,
        }
        kind = data["kind"]
        if kind not in kinds:
            raise ValueError(f"Неизвестный вид улики: {kind}")
        return kinds[kind].from_dict(data)


class PhysicalEvidence(Evidence):

    def __init__(self, evidence_type: EvidenceType, description: str,
                 found_at: Location, weight: float, storage_location: str,
                 entity_id: UUID | None = None,
                 created_at: datetime | None = None) -> None:
        super().__init__(evidence_type, description, found_at,
                         entity_id, created_at)
        self._weight = check_number(weight, "Вес")
        if self._weight < 0:
            raise ValueError("Вес улики не может быть отрицательным")
        self._storage_location = check_text(storage_location, "Хранилище")

    @property
    def weight(self) -> float:
        return self._weight

    @property
    def storage_location(self) -> str:
        return self._storage_location

    def get_summary(self) -> str:
        return (f"[Вещдок] {self.description}, {self._weight} кг, "
                f"хранится: {self._storage_location}")

    def to_dict(self) -> dict[str, Any]:
        data = self._base_dict()
        data["kind"] = "physical"
        data["weight"] = self._weight
        data["storage_location"] = self._storage_location
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PhysicalEvidence":
        return cls(
            EvidenceType(data["evidence_type"]),
            data["description"],
            Location.from_dict(data["found_at"]),
            data["weight"],
            data["storage_location"],
            UUID(data["id"]),
            datetime.fromisoformat(data["created_at"]),
        )


class DigitalEvidence(Evidence):

    def __init__(self, evidence_type: EvidenceType, description: str,
                 found_at: Location, file_hash: str, device: str,
                 entity_id: UUID | None = None,
                 created_at: datetime | None = None) -> None:
        super().__init__(evidence_type, description, found_at,
                         entity_id, created_at)
        self._file_hash = check_text(file_hash, "Хеш файла")
        self._device = check_text(device, "Устройство")

    @property
    def file_hash(self) -> str:
        return self._file_hash

    @property
    def device(self) -> str:
        return self._device

    def get_summary(self) -> str:
        return (f"[Цифровая] {self.description}, устройство: "
                f"{self._device}, хеш: {self._file_hash[:8]}...")

    def to_dict(self) -> dict[str, Any]:
        data = self._base_dict()
        data["kind"] = "digital"
        data["file_hash"] = self._file_hash
        data["device"] = self._device
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DigitalEvidence":
        return cls(
            EvidenceType(data["evidence_type"]),
            data["description"],
            Location.from_dict(data["found_at"]),
            data["file_hash"],
            data["device"],
            UUID(data["id"]),
            datetime.fromisoformat(data["created_at"]),
        )


# Восстановление человека по полю role (для допросов)
def person_from_dict(data: dict[str, Any]) -> Person:
    roles: dict[str, type[Person]] = {
        "detective": Detective,
        "suspect": Suspect,
        "witness": Witness,
    }
    role = data["role"]
    if role not in roles:
        raise ValueError(f"Неизвестная роль: {role}")
    return roles[role].from_dict(data)


# Допрос: кого, когда, стенограмма и длительность
class Interrogation(BaseEntity):

    def __init__(self, person: Person, conducted_at: datetime,
                 transcript: str, duration_minutes: int,
                 entity_id: UUID | None = None,
                 created_at: datetime | None = None) -> None:
        super().__init__(entity_id, created_at)
        if not isinstance(person, Person):
            raise TypeError("Допросить можно только человека (Person)")
        if not isinstance(conducted_at, datetime):
            raise TypeError("Время допроса должно быть datetime")
        self._person = person
        self._conducted_at = conducted_at
        self._transcript = check_text(transcript, "Стенограмма")
        self._duration_minutes = check_int(duration_minutes, "Длительность")
        if self._duration_minutes <= 0:
            raise ValueError("Длительность допроса должна быть больше 0")

    @property
    def person(self) -> Person:
        return self._person

    @property
    def conducted_at(self) -> datetime:
        return self._conducted_at

    @property
    def transcript(self) -> str:
        return self._transcript

    @property
    def duration_minutes(self) -> int:
        return self._duration_minutes

    def to_dict(self) -> dict[str, Any]:
        data = self._base_dict()
        data["person"] = self._person.to_dict()
        data["conducted_at"] = self._conducted_at.isoformat()
        data["transcript"] = self._transcript
        data["duration_minutes"] = self._duration_minutes
        return data

    # people — уже загруженные участники дела, чтобы не создавать копии
    @classmethod
    def from_dict(cls, data: dict[str, Any],
                  people: dict[UUID, Person] | None = None
                  ) -> "Interrogation":
        person_id = UUID(data["person"]["id"])
        if people is not None and person_id in people:
            person = people[person_id]
        else:
            person = person_from_dict(data["person"])
        return cls(
            person,
            datetime.fromisoformat(data["conducted_at"]),
            data["transcript"],
            data["duration_minutes"],
            UUID(data["id"]),
            datetime.fromisoformat(data["created_at"]),
        )

    def __str__(self) -> str:
        return (f"Допрос: {self._person}, "
                f"{self._conducted_at:%d.%m.%Y %H:%M}, "
                f"{self._duration_minutes} мин")