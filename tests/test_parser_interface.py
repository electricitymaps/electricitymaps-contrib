import glob
import inspect
import unittest
from inspect import isfunction
from pathlib import Path
from typing import Callable, List, NamedTuple

from electricitymap.contrib.config.model import CONFIG_MODEL

PARSER_FOLDERS = Path(__file__).parent.resolve() / "../parsers"
PARSER_FILES_GLOB = f"{PARSER_FOLDERS.resolve()}/*.py"
_PARSER_FUNCTION_ARGS = ["zone_key", "session", "target_datetime", "logger"]
_EXCHANGE_FUNCTION_ARGS = [
    "zone_key1",
    "zone_key2",
    "session",
    "target_datetime",
    "logger",
]
EXPECTED_MODE_FUNCTION_ARGS = {
    "consumption": _PARSER_FUNCTION_ARGS,
    "consumptionForecast": _PARSER_FUNCTION_ARGS,
    "exchange": _EXCHANGE_FUNCTION_ARGS,
    "exchangeForecast": _EXCHANGE_FUNCTION_ARGS,
    "generationForecast": _PARSER_FUNCTION_ARGS,
    "price": _PARSER_FUNCTION_ARGS,
    "production": _PARSER_FUNCTION_ARGS,
    "productionPerModeForecast": _PARSER_FUNCTION_ARGS,
    "productionPerUnit": _PARSER_FUNCTION_ARGS,
}
_RETURN_PARSER_TYPE = [dict, list, List[dict]]
EXPECTED_MODE_RETURN_ANNOTATIONS = {
    "consumption": _RETURN_PARSER_TYPE,
    "consumptionForecast": _RETURN_PARSER_TYPE,
    "exchange": _RETURN_PARSER_TYPE,
    "exchangeForecast": _RETURN_PARSER_TYPE,
    "generationForecast": _RETURN_PARSER_TYPE,
    "price": _RETURN_PARSER_TYPE,
    "production": _RETURN_PARSER_TYPE,
    "productionPerModeForecast": _RETURN_PARSER_TYPE,
    "productionPerUnit": _RETURN_PARSER_TYPE,
}


class ZoneParserFunction(NamedTuple):
    zone: str
    mode: str
    function_name: str
    function: Callable


def undecorated(o):
    """Remove all decorators from a function.
    Inspired by https://github.com/iartarisi/undecorated/blob/master/undecorated.py
    """

    closure = o.__closure__

    if closure:
        for cell in closure:
            if cell.cell_contents is o:
                continue

            if isfunction(cell.cell_contents):
                undecd = undecorated(cell.cell_contents)
                if undecd:
                    return undecd
        else:
            return o
    else:
        return o


class ParserInterfaceTestcase(unittest.TestCase):
    def setUp(self):
        self.zone_parser_functions: List[ZoneParserFunction] = []

        for model_map in [CONFIG_MODEL.exchanges, CONFIG_MODEL.zones]:
            for zone in model_map.keys():
                model = model_map[zone]
                if not model.parsers:
                    continue

                for mode, function_name in model.parsers:
                    if function_name is not None:
                        # load all functions
                        function = model.parsers.get_function(mode)
                        self.assertTrue(callable(function))
                        assert function

                        self.zone_parser_functions.append(
                            ZoneParserFunction(
                                zone=zone,
                                mode=mode,
                                function_name=function_name,
                                function=function,
                            )
                        )

    def test_interface(self):
        for zone_parser_function in self.zone_parser_functions:
            _zone, _mode, function_name, function = zone_parser_function

            # do a poor mans type checking (until we use MyPy or a similar tool)
            arg_spec = inspect.getfullargspec(undecorated(function))

            (
                args,
                varargs,
                varkw,
                defaults,
                _kwonlyargs,
                _kwonlydefaults,
                annotations,
            ) = arg_spec

            self.assertIsNone(
                varargs,
                f"expected no varargs for {function_name}, arg_spec={arg_spec}",
            )

            self.assertIsNone(
                varkw,
                f"expected no varkw for {function_name}, arg_spec={arg_spec}",
            )

            self.assertEqual(
                [a for a in args],
                EXPECTED_MODE_FUNCTION_ARGS[_mode],
                f"invalid args for {function_name}, arg_spec={arg_spec}",
            )

            if annotations and "return" in annotations:
                expected = EXPECTED_MODE_RETURN_ANNOTATIONS[_mode]
                correct_annotations = any(
                    [annotations["return"] == a for a in expected]
                )
                self.assertTrue(
                    correct_annotations,
                    f"expected annotation for {function_name} to be in {expected} not {annotations}",
                )

    def test_unused_files(self):
        parser_files_used = {
            f'{f.function_name.rsplit(".", 1)[0]}.py'
            for f in self.zone_parser_functions
        }

        all_parser_files = {
            f.rsplit("/", 1)[-1] for f in glob.glob(PARSER_FILES_GLOB)
        } - {"example.py", "__init__.py"}

        unused_parser_files = all_parser_files - parser_files_used

        print("> unused_parser_files", unused_parser_files)


if __name__ == "__main__":
    unittest.main(buffer=True)
