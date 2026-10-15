# Классы предметной области «Детективное агентство»
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


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


# Проверка: Enum, ошибки ValueError/TypeError, объект -> словарь -> объект
if __name__ == "__main__":
    for status in CaseStatus:
        print(status.name, "->", status.value)

    # строку из файла превращаем обратно в элемент перечисления
    print(CaseStatus("closed"))
    print(CasePriority.HIGH == CasePriority.HIGH)

    # несуществующий статус -> встроенная ошибка ValueError
    try:
        CaseStatus("lost")
    except ValueError as error:
        print("ValueError:", error)

    # объект абстрактного класса создать нельзя -> TypeError
    try:
        BaseEntity()
    except TypeError as error:
        print("TypeError:", error)

    # учебный наследник: реализует оба абстрактных метода
    class Note(BaseEntity):

        def __init__(self, text: str, entity_id: UUID | None = None,
                     created_at: datetime | None = None) -> None:
            super().__init__(entity_id, created_at)
            self.text = text

        def to_dict(self) -> dict[str, Any]:
            data = self._base_dict()
            data["text"] = self.text
            return data

        @classmethod
        def from_dict(cls, data: dict[str, Any]) -> "Note":
            return cls(data["text"], UUID(data["id"]),
                       datetime.fromisoformat(data["created_at"]))

    first = Note("Первая запись")
    second = Note("Вторая запись")
    print(first.id)
    print(second.id)
    # у каждого объекта свой уникальный номер
    print(first.id == second.id)
    print(first.to_dict())

    # после восстановления из словаря номер тот же
    restored = Note.from_dict(first.to_dict())
    print(restored.text, restored.id == first.id)