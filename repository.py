# Хранилище дел: CRUD и сохранение/загрузка в JSON и XML
import json
from xml.etree import ElementTree
from typing import Any
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

    # общая часть загрузки: из списка словарей собираем дела
    def _load_cases(self, items: list[dict[str, Any]]) -> None:
        loaded: dict[UUID, Case] = {}
        for number, item in enumerate(items, start=1):
            try:
                case = Case.from_dict(item)
            except KeyError as error:
                raise ValueError(
                    f"Дело №{number}: в данных нет поля {error}") from error
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"Дело №{number}: неверные данные ({error})") from error
            loaded[case.id] = case
        # заменяем содержимое, только если всё загрузилось без ошибок
        self._cases = loaded

    # --- JSON ---

    def save_to_json(self, path: str) -> None:
        data = {"cases": [case.to_dict() for case in self._cases.values()]}
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def load_from_json(self, path: str) -> None:
        # FileNotFoundError не ловим: о нём должен узнать вызывающий код
        with open(path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError as error:
                message = f"Файл {path} не является JSON: {error}"
                raise ValueError(message) from error
        try:
            items = data["cases"]
        except (KeyError, TypeError) as error:
            raise ValueError(f"В файле {path} нет списка cases") from error
        self._load_cases(items)

    # --- XML ---

    def save_to_xml(self, path: str) -> None:
        root = ElementTree.Element("agency")
        for case in self._cases.values():
            root.append(_to_xml("case", case.to_dict()))
        tree = ElementTree.ElementTree(root)
        ElementTree.indent(tree, space="    ")
        tree.write(path, encoding="utf-8", xml_declaration=True)

    def load_from_xml(self, path: str) -> None:
        try:
            root = ElementTree.parse(path).getroot()
        except ElementTree.ParseError as error:
            message = f"Файл {path} не является XML: {error}"
            raise ValueError(message) from error
        if root.tag != "agency":
            raise ValueError(f"Корневой тег должен быть agency, а не "
                             f"{root.tag}")
        items: list[dict[str, Any]] = []
        for element in root.findall("case"):
            value = _from_xml(element)
            if not isinstance(value, dict):
                raise ValueError("Тег case должен содержать поля дела")
            items.append(value)
        self._load_cases(items)


# В XML всё хранится текстом, поэтому у каждого тега пишем атрибут type,
# чтобы при чтении вернуть число числом, а список списком
def _to_xml(tag: str, value: Any) -> ElementTree.Element:
    element = ElementTree.Element(tag)
    if value is None:
        element.set("type", "none")
    elif isinstance(value, bool):
        element.set("type", "bool")
        element.text = "true" if value else "false"
    elif isinstance(value, int):
        element.set("type", "int")
        element.text = str(value)
    elif isinstance(value, float):
        element.set("type", "float")
        element.text = str(value)
    elif isinstance(value, str):
        element.set("type", "str")
        element.text = value
    elif isinstance(value, dict):
        element.set("type", "dict")
        for key, item in value.items():
            element.append(_to_xml(key, item))
    elif isinstance(value, list):
        element.set("type", "list")
        for item in value:
            element.append(_to_xml("item", item))
    else:
        raise TypeError(f"Нельзя записать в XML значение {value!r}")
    return element


def _from_xml(element: ElementTree.Element) -> Any:
    kind = element.get("type", "str")
    text = element.text or ""
    if kind == "none":
        return None
    if kind == "bool":
        return text == "true"
    if kind == "int":
        return int(text)
    if kind == "float":
        return float(text)
    if kind == "str":
        return text
    if kind == "dict":
        return {child.tag: _from_xml(child) for child in element}
    if kind == "list":
        return [_from_xml(child) for child in element]
    raise ValueError(f"Неизвестный тип в XML: {kind}")