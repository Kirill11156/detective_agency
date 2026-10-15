# Хранилище дел: CRUD (создание, чтение, обновление, удаление)
from uuid import UUID

from exceptions import CaseNotFoundError
from models import Case


class CaseRepository:

    def __init__(self) -> None:
        # словарь id -> дело: поиск по номеру сразу, без перебора списка
        self._cases: dict[UUID, Case] = {}

    # --- CRUD ---

    def create(self, case: Case) -> None:
        if not isinstance(case, Case):
            raise TypeError("В хранилище можно добавить только Case")
        if case.id in self._cases:
            raise ValueError(f"Дело «{case.title}» уже есть в хранилище")
        self._cases[case.id] = case

    def read(self, case_id: UUID) -> Case:
        # KeyError от словаря превращаем в понятную ошибку агентства
        try:
            return self._cases[case_id]
        except KeyError:
            raise CaseNotFoundError(case_id) from None

    def update(self, case: Case) -> None:
        if case.id not in self._cases:
            raise CaseNotFoundError(case.id)
        self._cases[case.id] = case

    def delete(self, case_id: UUID) -> None:
        if case_id not in self._cases:
            raise CaseNotFoundError(case_id)
        del self._cases[case_id]

    def get_all(self) -> list[Case]:
        return list(self._cases.values())

    def __len__(self) -> int:
        return len(self._cases)