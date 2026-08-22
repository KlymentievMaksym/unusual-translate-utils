import pathlib
from dataclasses import dataclass

from translate_utils.core.entities import TranslationsDicts
from translate_utils.core.interfaces import ParseStrategy
from translate_utils.infrastructure.io import read_renpy_file


@dataclass(frozen=True, slots=True)
class DirectoryCompareResult:
    added: list[str]
    deleted: list[str]
    changed: list[str]
    identical: list[str]


class CompareService:
    def __init__(self, parser: ParseStrategy[TranslationsDicts]):
        self._parser = parser

    def compare_directories(self, dir1: str, dir2: str) -> DirectoryCompareResult:
        path1 = pathlib.Path(dir1)
        path2 = pathlib.Path(dir2)

        # Знаходимо всі файли з розширенням .rpy (або іншим потрібним)
        files1 = {f.relative_to(path1) for f in path1.rglob("*.rpy") if f.is_file()}
        files2 = {f.relative_to(path2) for f in path2.rglob("*.rpy") if f.is_file()}

        # 1. Файли, які є тільки в одній з папок
        added = [str(f) for f in (files2 - files1)]
        deleted = [str(f) for f in (files1 - files2)]

        changed = []
        identical = []

        # 2. Файли, які є в обох папках (порівнюємо їхній вміст через парсер)
        common_files = files1 & files2

        for file_path in common_files:
            full_path1 = path1 / file_path
            full_path2 = path2 / file_path

            # Читаємо текст
            text1 = read_renpy_file(str(full_path1))
            text2 = read_renpy_file(str(full_path2))

            # Парсимо в TranslationsDicts
            dict1 = self._parser(file_text=text1)
            dict2 = self._parser(file_text=text2)

            # Завдяки dataclasses ми можемо просто порівняти два об'єкти!
            if dict1 == dict2:
                identical.append(str(file_path))
            else:
                changed.append(str(file_path))

        return DirectoryCompareResult(
            added=sorted(added),
            deleted=sorted(deleted),
            changed=sorted(changed),
            identical=sorted(identical),
        )
