# Агентство: детективы и дела (дела хранятся в CaseRepository)
from uuid import UUID

from models import Case, CaseStatus, Detective
from repository import CaseRepository


class Agency:

    def __init__(self, name: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Название агентства не может быть пустым")
        self._name = name.strip()
        self._repository = CaseRepository()
        self._detectives: list[Detective] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def repository(self) -> CaseRepository:
        return self._repository

    @property
    def cases(self) -> list[Case]:
        return self._repository.get_all()

    @property
    def detectives(self) -> list[Detective]:
        return list(self._detectives)

    def add_detective(self, detective: Detective) -> None:
        if not isinstance(detective, Detective):
            raise TypeError("Ожидался объект Detective")
        if any(d.id == detective.id for d in self._detectives):
            raise ValueError(f"{detective.name} уже работает в агентстве")
        self._detectives.append(detective)

    def add_case(self, case: Case) -> None:
        self._repository.create(case)

    def get_case(self, case_id: UUID) -> Case:
        return self._repository.read(case_id)

    def delete_case(self, case_id: UUID) -> None:
        self._repository.delete(case_id)

    # поиск через генератор списка с условием
    def find_case_by_status(self, status: CaseStatus) -> list[Case]:
        if not isinstance(status, CaseStatus):
            raise TypeError("Статус должен быть CaseStatus")
        return [case for case in self.cases if case.status == status]

    # сравниваем по id: после загрузки из файла объекты уже другие
    def find_cases_by_detective(self, detective: Detective) -> list[Case]:
        result: list[Case] = []
        for case in self.cases:
            lead = case.lead_detective
            if lead is not None and lead.id == detective.id:
                result.append(case)
        return result

    def get_open_cases(self) -> list[Case]:
        return [case for case in self.cases if not case.is_closed]

    # сортировка по приоритету: лямбда задаёт ключ сортировки
    def get_cases_by_priority(self) -> list[Case]:
        order = ["critical", "high", "medium", "low"]
        return sorted(self.cases,
                      key=lambda case: order.index(case.priority.value))

    def assign_lead_detective(self, case_id: UUID,
                              detective: Detective) -> None:
        if not any(d.id == detective.id for d in self._detectives):
            raise ValueError(f"{detective.name} не работает в агентстве")
        case = self.get_case(case_id)
        detective.take_case(case)