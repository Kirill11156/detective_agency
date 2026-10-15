# Демонстрация работы детективного агентства
import os
from datetime import datetime
from uuid import uuid4

from agency import Agency
from exceptions import AgencyError
from models import (
    Case,
    CasePriority,
    CaseStatus,
    DigitalEvidence,
    Detective,
    EvidenceType,
    Interrogation,
    Location,
    PhysicalEvidence,
    Specialization,
    Suspect,
    Witness,
)

JSON_FILE = "agency.json"
XML_FILE = "agency.xml"


# *parts — любое число строк заголовка, **options — настройки оформления
def print_header(*parts: str, **options: str) -> None:
    line = options.get("line", "=")
    title = " ".join(parts)
    print()
    print(line * 60)
    print(title)
    print(line * 60)


def create_agency() -> Agency:
    agency = Agency("Бейкер-стрит, 221Б")

    holmes = Detective("Шерлок Холмс", "+7 900 000-00-01",
                       Specialization.DETECTIVE, "Старший детектив", 12)
    watson = Detective("Джон Ватсон", "+7 900 000-00-02",
                       Specialization.FORENSIC, "Детектив", 3)
    lestrade = Detective("Инспектор Лестрейд", "+7 900 000-00-03",
                         Specialization.ANALYST, "Инспектор")
    for detective in (holmes, watson, lestrade):
        agency.add_detective(detective)

    # Дело 1: кража картины
    museum = Location("ул. Пречистенка, 10", "музей", 55.744, 37.597)
    theft = Case("Кража картины", museum, CasePriority.HIGH)
    ivan = Suspect("Иван Петров", "+7 911 111-11-11",
                   "был дома один", 40)
    anna = Suspect("Анна Смирнова", "+7 922 222-22-22",
                   "была на работе, есть пропуск", 20)
    guard = Witness("Пётр Сидоров", "+7 933 333-33-33",
                    "видел мужчину в сером пальто", 7)
    theft.add_suspect(ivan)
    theft.add_suspect(anna)
    theft.add_witness(guard)
    theft.add_evidence(PhysicalEvidence(
        EvidenceType.FINGERPRINT, "Отпечаток на раме", museum,
        0.01, "Сейф №3"))
    theft.add_evidence(DigitalEvidence(
        EvidenceType.DIGITAL, "Запись камеры у входа", museum,
        "a3f5c9d2e81b4f7a", "Камера №2"))
    theft.add_interrogation(Interrogation(
        ivan, datetime(2026, 10, 1, 14, 30),
        "Утверждает, что весь вечер был дома", 45))
    theft.add_interrogation(Interrogation(
        guard, datetime(2026, 10, 1, 16, 0),
        "Описал подозрительного мужчину у служебного входа", 30))
    agency.add_case(theft)

    # Дело 2: взлом почты
    office = Location("Пресненская наб., 12", "офис", 55.749, 37.539)
    hack = Case("Взлом корпоративной почты", office, CasePriority.CRITICAL)
    admin = Suspect("Олег Кузнецов", "+7 944 444-44-44",
                    "был в отпуске", 60)
    hack.add_suspect(admin)
    hack.add_evidence(DigitalEvidence(
        EvidenceType.DIGITAL, "Логи почтового сервера", office,
        "9b1e7c3f0a2d5e8b", "Сервер mail-01"))
    agency.add_case(hack)

    # Дело 3: пропажа собаки
    park = Location("Парк Горького", "улица", 55.729, 37.601)
    dog = Case("Пропажа собаки", park, CasePriority.LOW)
    neighbor = Witness("Мария Волкова", "+7 955 555-55-55",
                       "видела собаку у пруда", 4)
    dog.add_witness(neighbor)
    dog.add_evidence(PhysicalEvidence(
        EvidenceType.DOCUMENT, "Ошейник с жетоном", park,
        0.2, "Шкаф улик №1"))
    agency.add_case(dog)

    # Дело 4: подделка документов (пока без детектива)
    archive = Location("ул. Ильинка, 4", "квартира", 55.755, 37.625)
    fake = Case("Подделка завещания", archive)
    fake.add_evidence(PhysicalEvidence(
        EvidenceType.DOCUMENT, "Завещание с подписью", archive,
        0.05, "Сейф №1"))
    agency.add_case(fake)

    agency.assign_lead_detective(theft.id, holmes)
    agency.assign_lead_detective(hack.id, watson)
    agency.assign_lead_detective(dog.id, lestrade)
    return agency


def show_agency(agency: Agency) -> None:
    for case in agency.get_cases_by_priority():
        print(case.get_summary())
        print()


def demo_crud(agency: Agency) -> None:
    print_header("CRUD: создание, чтение, обновление, удаление")
    holmes = agency.detectives[0]

    # Read
    theft = agency.find_cases_by_detective(holmes)[0]
    same = agency.get_case(theft.id)
    print("Прочитано дело:", same.title)

    # Update: детектив раскрыл дело, подозрения сняты с невиновной
    anna = theft.suspects[1]
    anna.clear_suspect()
    theft.suspects[0].raise_suspicion(50)
    holmes.close_case(theft)
    agency.repository.update(theft)
    print(f"Дело «{theft.title}» закрыто, у {holmes.name} "
          f"раскрыто дел: {holmes.solved_cases}")

    # Create + Delete
    temp = Case("Учебное дело", Location("ул. Тестовая, 1", "офис", 0, 0))
    agency.add_case(temp)
    print("Дел после добавления:", len(agency.cases))
    agency.delete_case(temp.id)
    print("Дел после удаления:", len(agency.cases))

    print("Открытые дела:", [c.title for c in agency.get_open_cases()])
    print("Закрытые дела:",
          [c.title for c in agency.find_case_by_status(CaseStatus.CLOSED)])


def demo_exceptions(agency: Agency) -> None:
    print_header("Обработка исключений")
    theft = agency.find_case_by_status(CaseStatus.CLOSED)[0]
    museum = theft.location

    # каждое действие заведомо ошибочное; ловим и печатаем ошибку
    attempts = [
        ("улика в закрытое дело", lambda: theft.add_evidence(
            PhysicalEvidence(EvidenceType.WEAPON, "Нож", museum,
                             0.3, "Сейф №2"))),
        ("поиск несуществующего дела", lambda: agency.get_case(uuid4())),
        ("поиск несуществующей улики", lambda: theft.find_evidence(uuid4())),
        ("подозрение 150", lambda: Suspect(
            "Тест", "-", "нет", 150)),
        ("надёжность 0", lambda: Witness("Тест", "-", "нет", 0)),
        ("повторное оправдание", lambda: theft.suspects[1].clear_suspect()),
        ("пустое имя (ValueError)", lambda: Witness("", "-", "нет", 5)),
        ("строка вместо числа (TypeError)",
         lambda: Witness("Тест", "-", "нет", "десять")),
        ("пустая стенограмма (ValueError)", lambda: Interrogation(
            theft.suspects[0], datetime.now(), "   ", 10)),
    ]
    for title, action in attempts:
        try:
            action()
            print(f"{title}: ошибки не было")
        # свои исключения ловим одним except через базовый класс
        except AgencyError as error:
            print(f"{title} -> {type(error).__name__}: {error}")
        # встроенные исключения Python
        except (ValueError, TypeError) as error:
            print(f"{title} -> {type(error).__name__}: {error}")


def demo_files(agency: Agency) -> None:
    print_header("Сохранение и загрузка: JSON и XML")
    agency.repository.save_to_json(JSON_FILE)
    agency.repository.save_to_xml(XML_FILE)
    print(f"Сохранено дел: {len(agency.cases)} -> {JSON_FILE}, {XML_FILE}")

    from_json = Agency("Загружено из JSON")
    from_json.repository.load_from_json(JSON_FILE)
    from_xml = Agency("Загружено из XML")
    from_xml.repository.load_from_xml(XML_FILE)

    # сравниваем словари исходных и загруженных дел
    same_json = all(from_json.get_case(c.id).to_dict() == c.to_dict()
                    for c in agency.cases)
    same_xml = all(from_xml.get_case(c.id).to_dict() == c.to_dict()
                   for c in agency.cases)
    print("JSON совпадает с исходными данными:", same_json)
    print("XML совпадает с исходными данными:", same_xml)

    closed = from_json.find_case_by_status(CaseStatus.CLOSED)[0]
    print(f"После загрузки дело «{closed.title}» по-прежнему закрыто:",
          closed.is_closed)

    # ошибки работы с файлами
    for loader, path in [(from_json.repository.load_from_json, "nope.json"),
                         (from_xml.repository.load_from_xml, "nope.xml")]:
        try:
            loader(path)
        except FileNotFoundError as error:
            print("FileNotFoundError:", error.filename)

    with open("broken.json", "w", encoding="utf-8") as file:
        file.write('{"cases": [{"title": "Без остальных полей"}]}')
    try:
        from_json.repository.load_from_json("broken.json")
    except ValueError as error:
        print("Повреждённый JSON ->", error)
        print("  причина:", type(error.__cause__).__name__)

    with open("broken.xml", "w", encoding="utf-8") as file:
        file.write("<agency><case>")
    try:
        from_xml.repository.load_from_xml("broken.xml")
    except ValueError as error:
        print("Повреждённый XML ->", error)

    # учебные испорченные файлы больше не нужны
    os.remove("broken.json")
    os.remove("broken.xml")


def main() -> None:
    agency = create_agency()
    print_header("Агентство", agency.name)
    show_agency(agency)
    demo_crud(agency)
    demo_exceptions(agency)
    demo_files(agency)
    print_header("Готово", line="-")


if __name__ == "__main__":
    main()