# Собственные исключения детективного агентства.
# Все наследуются от AgencyError, чтобы их можно было ловить одним except.
from uuid import UUID


# Базовое исключение агентства, родитель для всех остальных
class AgencyError(Exception):

    def __init__(self, message: str) -> None:
        super().__init__(message)
        # храним текст отдельно, чтобы обращаться к нему как error.message
        self.message = message


# Наследники принимают данные об ошибке, а текст сообщения собирают сами
class CaseNotFoundError(AgencyError):

    def __init__(self, case_id: UUID) -> None:
        super().__init__(f"Дело с id={case_id} не найдено")
        self.case_id = case_id


class CaseAlreadyClosedError(AgencyError):

    def __init__(self, case_title: str) -> None:
        super().__init__(f"Дело «{case_title}» уже закрыто")
        self.case_title = case_title


class EvidenceNotFoundError(AgencyError):

    def __init__(self, evidence_id: UUID) -> None:
        super().__init__(f"Улика с id={evidence_id} не найдена")
        self.evidence_id = evidence_id


class InvalidSuspicionLevelError(AgencyError):

    def __init__(self, value: int) -> None:
        super().__init__(f"Подозрение должно быть от 0 до 100, а не {value}")
        self.value = value


class SuspectAlreadyClearedError(AgencyError):

    def __init__(self, suspect_name: str) -> None:
        super().__init__(f"Подозреваемый {suspect_name} уже оправдан")
        self.suspect_name = suspect_name


class InvalidReliabilityError(AgencyError):

    def __init__(self, value: int) -> None:
        super().__init__(f"Надёжность должна быть от 1 до 10, а не {value}")
        self.value = value


# Проверяем, выполняется только при запуске этого файла, не при импорте
if __name__ == "__main__":
    from uuid import uuid4

    try:
        raise InvalidSuspicionLevelError(150)
    except InvalidSuspicionLevelError as error:
        print("Поймали:", error)
        print("Неверное значение:", error.value)

    errors: list[AgencyError] = [
        CaseNotFoundError(uuid4()),
        CaseAlreadyClosedError("Кража картины"),
        SuspectAlreadyClearedError("Иван Петров"),
        InvalidReliabilityError(0),
    ]
    # Ловим по родителю AgencyError и перехватываются все наши исключения
    for err in errors:
        try:
            raise err
        except AgencyError as error:
            print(f"[{type(error).__name__}] {error.message}")