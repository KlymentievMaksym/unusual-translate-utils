import pathlib
from dataclasses import dataclass

from translate_utils.core.cleaner import TranslationCleaner
from translate_utils.core.entities import TranslationsDicts
from translate_utils.core.interfaces import ParseStrategy, ReadStrategy


@dataclass(frozen=True, slots=True)
class DirectoryCompareResult:
    added: list[str]
    deleted: list[str]
    changed: list[str]
    identical: list[str]


class CompareService:
    def __init__(
        self,
        file_reader: ReadStrategy[str],
        file_parser: ParseStrategy[TranslationsDicts],
        file_cleaner: TranslationCleaner,
    ) -> None:

        self._file_reader = file_reader
        self._file_parser = file_parser
        self._file_cleaner = file_cleaner

    def compare_directories(self, dir1: str, dir2: str) -> DirectoryCompareResult:
        path1 = pathlib.Path(dir1)
        path2 = pathlib.Path(dir2)

        files1 = {f.relative_to(path1) for f in path1.rglob("*.rpy") if f.is_file()}
        files2 = {f.relative_to(path2) for f in path2.rglob("*.rpy") if f.is_file()}

        added = [str(f) for f in (files2 - files1)]
        deleted = [str(f) for f in (files1 - files2)]

        changed = []
        identical = []

        common_files = files1 & files2

        for file_path in common_files:
            full_path1 = path1 / file_path
            full_path2 = path2 / file_path

            text1 = self._file_reader(full_path1)
            text2 = self._file_reader(full_path2)

            dict1 = self._file_parser(text1)
            dict2 = self._file_parser(text2)

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
