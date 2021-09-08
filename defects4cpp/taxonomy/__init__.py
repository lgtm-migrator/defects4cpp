import enum
import json
from collections.abc import MutableMapping
from dataclasses import dataclass
from os.path import dirname, exists, join
from pkgutil import iter_modules
from typing import Dict, List, Optional

import config
import errors


class TestType(enum.IntEnum):
    Automake = 1
    CTest = 2
    GoogleTest = 3


@dataclass
class Common:
    build_command: List[str]
    build_coverage_command: List[str]
    test_type: TestType
    test_command: List[str]
    test_coverage_command: List[str]
    gcov: "Gcov"


@dataclass
class Gcov:
    exclude: List[str]
    command: List[str]


@dataclass
class Defect:
    hash: str
    buggy_patch: str
    split_patch: str
    cases: int


@dataclass
class MetaInfo:
    url: str
    description: str
    vcs: str


class MetaData:
    def __init__(self, name: str, path: str):
        self.name = name
        self._path: str = path
        self._info: Optional[MetaInfo] = None
        self._common: Optional[Common] = None
        self._defects: List[Defect] = []

    @property
    def dockerfile(self) -> str:
        return f"{self._path}/Dockerfile"

    @property
    def info(self):
        if not self._info:
            self._load()
        return self._info

    @property
    def common(self):
        if not self._common:
            self._load()
        return self._common

    @property
    def defects(self):
        if not self._defects:
            self._load()
        return self._defects

    def _load(self):
        with open(f"{self._path}/meta.json", "r", encoding="utf-8") as fp:
            meta = json.load(fp)
        self._load_info(meta)
        self._load_common(meta)
        self._load_defects(meta)

    def _load_info(self, meta: Dict):
        try:
            self._defects = [
                Defect(
                    defect["hash"],
                    f"{self._path}/patch/{defect['patch']:04}-buggy.patch",
                    f"{self._path}/patch/{defect['patch']:04}-split.patch",
                    defect["cases"],
                )
                for defect in meta["defects"]
            ]
        except KeyError as e:
            raise errors.DppTaxonomyInitError(e.args[0], MetaInfo.__name__)

    def _load_common(self, meta: Dict):
        def replace_make_job_flags(options: List[str]) -> List[str]:
            return [
                opt.replace("@DPP_MAKE_JOB@", config.DPP_MAKE_JOB) for opt in options
            ]

        def to_enum(value: str) -> TestType:
            if value == "automake":
                return TestType.Automake
            elif value == "ctest":
                return TestType.CTest
            elif value == "gtest":
                return TestType.GoogleTest

        try:
            self._common = Common(
                replace_make_job_flags(meta["common"]["build"]["command"]),
                replace_make_job_flags(meta["common"]["build-coverage"]["command"]),
                to_enum(meta["common"]["test-type"]),
                replace_make_job_flags(meta["common"]["test"]["command"]),
                replace_make_job_flags(meta["common"]["test-coverage"]["command"]),
                Gcov(
                    [d for d in meta["common"]["gcov"]["exclude"]],
                    meta["common"]["gcov"]["command"],
                ),
            )
        except KeyError as e:
            raise errors.DppTaxonomyInitError(e.args[0], Common.__name__)

    def _load_defects(self, meta: Dict):
        try:
            self._info = MetaInfo(
                meta["info"]["url"], meta["info"]["short-desc"], meta["info"]["vcs"]
            )
        except KeyError as e:
            raise errors.DppTaxonomyInitError(e.args[0], Defect.__name__)


class Taxonomy(MutableMapping):
    def __init__(self, *args, **kwargs):
        self.base: str = dirname(__file__)
        self.store: Dict[str, MetaData] = dict(
            [
                (name, MetaData(name, f"{join(self.base, name)}"))
                for _, name, _ in iter_modules([dirname(__file__)])
            ]
        )
        # self.update(dict(*args, **kwargs))

    def __getitem__(self, key: str) -> MetaData:
        return self.store[self._keytransform(key)]

    def __setitem__(self, key: str, value: MetaData) -> None:
        # self.store[self._keytransform(key)] = value
        raise RuntimeError("set operator is not allowed")

    def __delitem__(self, key: str) -> None:
        # del self.store[self._keytransform(key)]
        raise RuntimeError("del operator is not allowed")

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def _keytransform(self, key: str):
        assert exists(
            join(self.base, key, "meta.json")
        ), f"Taxonomy '{key}' does not exist"
        return key


__all__ = ["Taxonomy", "MetaData", "MetaInfo", "Defect", "Common"]
