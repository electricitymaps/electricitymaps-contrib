import glob
import inspect
import unittest
from inspect import isfunction
from pathlib import Path
from typing import Callable, List, NamedTuple

from electricitymap.contrib.config.model import CONFIG_MODEL

PARSER_FOLDERS = Path(__file__).parent.resolve() / "../parsers"
PARSER_FILES_GLOB = f"{PARSER_FOLDERS.resolve()}/*.py"
EXPECTED_PARSER_FUNCTION_ARGS = ["zone_key", "session", "target_datetime", "logger"]
EXPECTED_MODE_ANNOTATIONS = {
    "consumption": {"return": dict},
    "exchange": {"return": list},
    "generationForecast": {"return": list},
    "price": dict,
    "production": {"return": list},
    "productionPerModeForecast": {"return": list},
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

            # if args != EXPECTED_PARSER_FUNCTION_ARGS:
            #     print(
            #         f"invalid args for {function_name}:\n{args}\n{EXPECTED_PARSER_FUNCTION_ARGS}\n"
            #     )
            #     # TODO: assert
            # self.assertEqual(
            #     args,
            #     MODE_TO_ARGS[mode],
            #     f"invalid args for {function_name}, arg_spec={arg_spec}",
            # )

            # if annotations:
            #     print("annotations", _mode, annotations)
            #     expected = EXPECTED_MODE_ANNOTATIONS[_mode]
            #     self.assertEqual(
            #         annotations,
            #         EXPECTED_MODE_ANNOTATIONS[_mode],
            #         f"expected annotation for {function_name} to be {expected} not {annotations}",
            #     )

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
        # TODO: assert


if __name__ == "__main__":
    unittest.main(buffer=True)
