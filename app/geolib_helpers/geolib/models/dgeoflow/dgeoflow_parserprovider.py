import logging
from os import path
from os import scandir
from typing import List
from typing import Tuple
from typing import Type
from typing import _GenericAlias
from typing import get_type_hints
from zipfile import ZipFile

from geolib.models.parsers import BaseParser
from geolib.models.parsers import BaseParserProvider
from geolib.models.utils import get_filtered_type_hints
from pydantic import DirectoryPath
from pydantic import FilePath
from zipp import Path

from .internal import BaseModelStructure
from .internal import DGeoflowStructure

logger = logging.getLogger(__name__)


class DGeoflowParser(BaseParser):
    @property
    def suffix_list(self) -> List[str]:
        return [".json", ""]

    @property
    def structure(self) -> Type[DGeoflowStructure]:
        return DGeoflowStructure

    def can_parse(self, filename: FilePath) -> bool:
        return super().can_parse(filename) or filename.is_dir()

    def parse(self, filepath: DirectoryPath) -> BaseModelStructure:
        ds = {}

        # Find required .json files via type hints
        for field, fieldtype in get_filtered_type_hints(self.structure):

            # On List types, parse a folder
            if type(fieldtype) == _GenericAlias:  # quite hacky
                element_type, *_ = fieldtype.__args__  # use getargs in 3.8
                ds[field] = self.__parse_folder(element_type, filepath / "")

            # Otherwise its a single .json in the root folder
            else:
                fn = filepath / (fieldtype.structure_name() + ".json")
                if not fn.exists():
                    raise FileNotFoundError(f"Couldn't find required file at {fn}")
                ds[field] = fieldtype.parse_raw(fn.open().read())

        return self.structure(**ds)

    def __parse_folder(self, fieldtype, filepath: DirectoryPath) -> List:
        out = []
        folder = filepath / fieldtype.structure_group()

        try:
            files = list(folder.iterdir())
        except FileNotFoundError:  # Not all result folders are required.
            return out

        # We need to sort to make sure that files such as x.json, x_1.json,
        # x_2.json etc. are stored sequentally, scandir produces arbitrary order.
        sorted_files = sorted(files, key=lambda x: x.name)
        for file in sorted_files:
            if fieldtype.structure_name() in file.name:
                out.append(fieldtype.parse_raw(file.open().read()))
            else:
                logger.debug(f"Didn't match {fieldtype} for {file}")

        if len(out) == 0:
            logger.debug(f"Couldn't find {fieldtype} file(s) at {folder}")

        return out


class DGeoflowZipParser(DGeoflowParser):
    @property
    def suffix_list(self) -> List[str]:
        return [".stix"]

    def can_parse(self, filename: FilePath) -> bool:
        return filename.suffix in self.suffix_list

    def parse(self, filepath: FilePath) -> BaseModelStructure:
        with ZipFile(filepath) as zip:

            # Fix backslashes in zipfile (untill fixed in DGeoflow)
            for file in zip.filelist:
                new_filename = file.filename.replace("\\", "/")
                if new_filename != file.filename:
                    file.filename = new_filename
            for key in list(zip.NameToInfo.keys()):
                new_key = key.replace("\\", "/")
                if new_key != key:
                    zip.NameToInfo[new_key] = zip.NameToInfo.pop(key)

            path = Path(zip)
            ds = super().parse(path)
        return ds


class DGeoflowParserProvider(BaseParserProvider):

    _input_parsers = None
    _output_parsers = None

    @property
    def input_parsers(self) -> Tuple[DGeoflowParser, DGeoflowZipParser]:
        if not self._input_parsers:
            self._input_parsers = (DGeoflowZipParser(), DGeoflowParser())
        return self._input_parsers

    @property
    def output_parsers(self) -> Tuple[DGeoflowParser, DGeoflowZipParser]:
        if not self._output_parsers:
            self._output_parsers = (DGeoflowParser(), DGeoflowZipParser())
        return self._output_parsers

    @property
    def parser_name(self) -> str:
        return "DGeoflow"
