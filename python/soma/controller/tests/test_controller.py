import json
import unittest

try:
    import pydantic.v1 as pydantic
except ImportError:
    import pydantic

from soma.controller import (
    Controller,
    Dict,
    Directory,
    File,
    List,
    Literal,
    OpenKeyController,
    Set,
    Union,
    field,
)
from soma.singleton import Singleton
from soma.undefined import undefined


class SubController(Controller):
    dummy: str


class SerializableController(Controller):
    s: str
    i: int
    n: float
    b: bool
    e: Literal["one", "two", "three"]
    f: File
    d: Directory
    u: Union[str, List[str]]
    m: dict
    lm: list[dict]
    mt: Dict[str, List[int]]
    l: list
    ll: List[List[str]]
    c: Controller
    lc: List[Controller]
    o: SubController
    lo: List[SubController]
    set_str: Set[str]
    set: set


class TestController(unittest.TestCase):
    def test_controller(self):
        c1 = Controller()
        c1.add_field("gogo", str)
        c1.add_field("bozo", int, 12)
        self.assertEqual(c1.gogo, undefined)
        self.assertEqual(c1.bozo, 12)
        self.assertEqual([i.name for i in c1.fields()], ["gogo", "bozo"])
        c1.gogo = "blop krok"
        self.assertEqual(c1.gogo, "blop krok")
        d = c1.asdict()
        self.assertEqual(d, {"gogo": "blop krok", "bozo": 12})
        c1.reorder_fields(["bozo", "gogo"])
        self.assertEqual([i.name for i in c1.fields()], ["bozo", "gogo"])
        c1.reorder_fields(["gogo", "bozo"])
        self.assertEqual([i.name for i in c1.fields()], ["gogo", "bozo"])

    def test_controller2(self):
        class Zuzur(Controller):
            glop: str = "zut"

        c2 = Zuzur()
        c3 = Zuzur()
        self.assertEqual(c2.glop, "zut")
        c2.glop = "I am c2"
        c3.glop = "I am c3"
        self.assertEqual(c2.glop, "I am c2")
        self.assertEqual(c3.glop, "I am c3")

    def test_controller3(self):
        class Babar(Controller):
            hupdahup: str = "barbatruc"
            gargamel: str
            ouioui: List[str]
            yes_or_no: Literal["yes", "no"]

        c1 = Babar()
        d = c1.asdict()
        self.assertEqual(d, {"hupdahup": "barbatruc"})
        c2 = Babar()
        c2.gargamel = "schtroumpf"
        c2.import_dict(d, clear=True)
        self.assertEqual(c2.asdict(), d)
        c2.gargamel = "schtroumpf"
        c2.import_dict(d)
        c2.ouioui = []
        self.assertEqual(
            c2.asdict(exclude_empty=True),
            {"hupdahup": "barbatruc", "gargamel": "schtroumpf"},
        )
        c1.yes_or_no = "yes"
        c1.yes_or_no = "no"
        c1.yes_or_no = undefined
        del c1.yes_or_no
        self.assertRaises(
            pydantic.ValidationError, setattr, c1, "yes_or_no", "bad value"
        )

    def test_controller4(self):
        class Driver(Controller):
            head: str = ""
            arms: str = ""
            legs: str = ""

        class Car(Controller):
            wheels: str
            engine: str
            driver: Driver = field(
                default_factory=lambda: Driver(),
                doc="the guy who would better take a bus",
            )
            problems: OpenKeyController

        my_car = Car()
        my_car.wheels = "flat"
        my_car.engine = "wind-broken"
        my_car.driver.head = "empty"
        my_car.driver.arms = "heavy"
        my_car.driver.legs = "short"
        my_car.problems = {"exhaust": "smoking", "windshield": "cracked"}
        d = my_car.asdict()
        self.assertEqual(
            d,
            {
                "wheels": "flat",
                "engine": "wind-broken",
                "driver": {"head": "empty", "arms": "heavy", "legs": "short"},
                "problems": {"exhaust": "smoking", "windshield": "cracked"},
            },
        )
        self.assertTrue(isinstance(my_car.driver, Driver))
        self.assertTrue(isinstance(my_car.problems, OpenKeyController))
        my_car.driver = {"head": "smiling", "legs": "strong"}
        d = my_car.asdict()
        self.assertEqual(
            d,
            {
                "wheels": "flat",
                "engine": "wind-broken",
                "driver": {"head": "smiling", "arms": "", "legs": "strong"},
                "problems": {"exhaust": "smoking", "windshield": "cracked"},
            },
        )

        other_car = my_car.copy(with_values=True)
        self.assertEqual(other_car.asdict(), d)
        other_car = my_car.copy(with_values=False)
        self.assertEqual(
            other_car.asdict(), {"driver": {"head": "", "arms": "", "legs": ""}}
        )

        my_car.problems.fuel = 3.5
        self.assertEqual(my_car.problems.fuel, "3.5")
        self.assertRaises(ValueError, setattr, my_car.problems, "fuel", {})
        del my_car.problems.fuel
        self.assertEqual(
            [i.name for i in my_car.problems.fields()], ["exhaust", "windshield"]
        )

        self.assertEqual(
            my_car.field("driver").doc, "the guy who would better take a bus"
        )
        manhelp = my_car.field_doc("driver")
        self.assertEqual(
            manhelp,
            f"driver [Controller[{__name__}.Driver]]: the guy who would better take a bus",
        )

    def test_dynamic_controllers(self):
        class C(Controller):
            static_int: int = 0
            static_str: str
            static_list: list = field(default_factory=lambda: [])
            static_dict: dict = field(default_factory=lambda: {})

        o = C(static_str="")

        o.add_field("dynamic_int", int, default=0)
        o.add_field("dynamic_str", str, default="default", custom_attribute=True)
        o.add_field("dynamic_list", List[int])
        self.assertEqual(o.field("dynamic_str").metadata("custom_attribute"), True)

        calls = []
        o.on_attribute_change.add(lambda: calls.append([]))
        o.on_attribute_change.add(lambda one: calls.append([one]))
        o.on_attribute_change.add(lambda one, two: calls.append([one, two]))
        o.on_attribute_change.add(
            lambda one, two, three: calls.append([one, two, three])
        )
        o.on_attribute_change.add(
            lambda one, two, three, four: calls.append([one, two, three, four])
        )
        o.on_attribute_change.add(
            lambda one, two, three, four, five: calls.append(
                [one, two, three, four, five]
            )
        )
        self.assertRaises(
            ValueError,
            o.on_attribute_change.add,
            lambda one, two, three, four, five, six: calls.append(
                [one, two, three, four, five, six]
            ),
        )

        o.static_int = 0
        o.static_int = 42
        o.static_int = 42
        o.anything = "x"
        self.assertRaises(pydantic.ValidationError, setattr, o, "dynamic_int", "toto")
        o.dynamic_str = "x"

        self.maxDiff = 1000
        self.assertEqual(
            calls,
            [
                [],
                [42],
                [42, 0],
                [42, 0, "static_int"],
                [42, 0, "static_int", o],
                [42, 0, "static_int", o, None],
                [],
                ["x"],
                ["x", "default"],
                ["x", "default", "dynamic_str"],
                ["x", "default", "dynamic_str", o],
                ["x", "default", "dynamic_str", o, None],
            ],
        )

        n = "dynamic_int"
        f = o.field(n)
        self.assertEqual(f.name, "dynamic_int")
        self.assertEqual(f.type, int)
        self.assertEqual(f.default, 0)
        self.assertEqual(f.metadata("class_field"), False)

        n = "dynamic_str"
        f = o.field(n)
        self.assertEqual(f.name, "dynamic_str")
        self.assertEqual(f.type, str)
        self.assertEqual(f.default, "default")
        self.assertEqual(f.metadata("class_field"), False)
        self.assertEqual(f.metadata("custom_attribute"), True)

        n = "static_dict"
        f = o.field(n)
        self.assertEqual(f.name, "static_dict")
        self.assertEqual(f.type, dict)
        self.assertEqual(f.default_factory(), {})
        self.assertEqual(f.metadata("class_field"), True)

        n = "static_list"
        f = o.field(n)
        self.assertEqual(f.name, "static_list")
        self.assertEqual(f.type, list)
        self.assertEqual(f.default_factory(), [])
        self.assertEqual(f.metadata("class_field"), True)

        n = "dynamic_list"
        f = o.field("dynamic_list")
        self.assertEqual(f.name, "dynamic_list")
        self.assertEqual(f.type, List[int])
        self.assertEqual(f.default, undefined)
        self.assertEqual(f.metadata("class_field"), False)

    def test_open_key_controller(self):
        class ControllerOfController(OpenKeyController[OpenKeyController]):
            static: str = "present"

        o = ControllerOfController()
        o.new_controller = {"first": 1, "second": "two"}
        self.assertEqual(o.static, "present")
        self.assertEqual([i.name for i in o.fields()], ["static", "new_controller"])
        self.assertEqual(o.new_controller.asdict(), {"first": "1", "second": "two"})

    def test_field_doc(self):
        class Blop(Controller):
            pass

        class C(Controller):
            f1: field(type_=float, default=5, doc="bla", optional=True, output=True)
            f2: field(type_=float, default=5, optional=False, output=True)

            f3: field(type_=Blop, default=None, metadata={"output": False})

            f4: field(type_=Union[str, int], metadata={"output": False})

        o = C()
        self.assertEqual(o.field_doc("f1"), "f1 [float] (5): bla")

        self.assertEqual(o.field_doc("f2"), "f2 [float] mandatory (5)")

        self.assertEqual(
            o.field_doc("f3"), f"f3 [Controller[{Blop.__module__}.Blop]] (None)"
        )

        self.assertEqual(o.field_doc("f4"), "f4 [Union[str,int]] mandatory")

    def test_inheritance(self):
        class Base(Controller):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)

            base1: str
            base2: str = "base2"

        class Derived(Base):
            derived1: str
            derived2: str = "derived2"

        o = Base()
        o = Derived()
        o.add_field("instance1", str)
        o.add_field("instance2", str, default="instance2")
        self.assertEqual(
            [i.name for i in o.fields()],
            ["base1", "base2", "derived1", "derived2", "instance1", "instance2"],
        )
        self.assertEqual(
            o.asdict(),
            {"base2": "base2", "derived2": "derived2", "instance2": "instance2"},
        )

    def test_modify_metadata(self):
        class C(Controller):
            s: field(type_=str, default="", custom="value")

        o = C()
        o.add_field("d", str, another="value")

        o.field("s").new = "value"
        o.field("s").custom = "modified"
        o.field("d").new = "value"
        o.field("d").another = "modified"
        self.assertEqual(o.field("s").class_field, True)
        self.assertEqual(o.field("s").custom, "modified")
        self.assertEqual(o.field("s").new, "value")
        self.assertEqual(o.field("d").class_field, False)
        self.assertEqual(o.field("d").another, "modified")
        self.assertEqual(o.field("d").new, "value")
        self.assertGreater(o.field("d").order, o.field("s").order)

    def test_field_types(self):
        class C(Controller):
            s: str
            os: field(type_=str, output=True)
            ls: List[str]
            ols: field(type_=List[str], output=True)

            i: int
            oi: field(type_=int, output=True)
            li: List[int]
            oli: field(type_=List[int], output=True)

            n: float
            on: field(type_=float, output=True)
            ln: list[float]
            oln: field(type_=List[float], output=True)

            b: bool
            ob: field(type_=bool, output=True)
            lb: list[bool]
            olb: field(type_=List[bool], output=True)

            e: Literal["one", "two", "three"]
            oe: field(type_=Literal["one", "two", "three"], output=True)
            le: List[Literal["one", "two", "three"]]
            ole: field(type_=List[Literal["one", "two", "three"]], output=True)

            f: File
            of: field(type_=File, write=True)
            lf: List[File]
            olf: field(type_=List[File], write=True)

            d: Directory
            od: field(type_=Directory, write=True)
            ld: List[Directory]
            old: field(type_=List[Directory], write=True)

            u: Union[str, List[str]]
            ou: field(type_=Union[str, List[str]], output=True)
            lu: List[Union[str, List[str]]]
            olu: field(type_=List[Union[str, List[str]]], output=True)

            m: Dict
            om: field(type_=dict, output=True)
            lm: List[dict]
            olm: field(type_=List[dict], output=True)
            mt: Dict[str, List[int]]

            l: list
            ll: List[List[str]]

            c: Controller
            lc: List[Controller]
            o: SubController
            lo: List[SubController]

            Set: Set
            Set_str: Set[str]
            set: set

        o = C()
        d = {
            f.name: {
                "name": f.name,
                "str": f.type_str(),
                "list": f.is_list(),
                "path_type": f.path_type,
                "is_path": f.is_path(),
                "is_file": f.is_file(),
                "is_directory": f.is_directory(),
                "output": f.is_output(),
            }
            for f in o.fields()
        }
        expected = {
            "s": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "s",
                "output": False,
                "str": "str",
            },
            "os": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "os",
                "output": True,
                "str": "str",
            },
            "ls": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "ls",
                "output": False,
                "str": "List[str]",
            },
            "ols": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "ols",
                "output": True,
                "str": "List[str]",
            },
            "i": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "i",
                "output": False,
                "str": "int",
            },
            "oi": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "oi",
                "output": True,
                "str": "int",
            },
            "li": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "li",
                "output": False,
                "str": "List[int]",
            },
            "oli": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "oli",
                "output": True,
                "str": "List[int]",
            },
            "n": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "n",
                "output": False,
                "str": "float",
            },
            "on": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "on",
                "output": True,
                "str": "float",
            },
            "ln": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "ln",
                "output": False,
                "str": "list[float]",
            },
            "oln": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "oln",
                "output": True,
                "str": "List[float]",
            },
            "b": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "b",
                "output": False,
                "str": "bool",
            },
            "ob": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "ob",
                "output": True,
                "str": "bool",
            },
            "lb": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "lb",
                "output": False,
                "str": "list[bool]",
            },
            "olb": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "olb",
                "output": True,
                "str": "List[bool]",
            },
            "e": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "e",
                "output": False,
                "str": "Literal['one','two','three']",
            },
            "oe": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "oe",
                "output": True,
                "str": "Literal['one','two','three']",
            },
            "le": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "le",
                "output": False,
                "str": "List[Literal['one','two','three']]",
            },
            "ole": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "ole",
                "output": True,
                "str": "List[Literal['one','two','three']]",
            },
            "f": {
                "path_type": "file",
                "is_path": True,
                "is_directory": False,
                "is_file": True,
                "list": False,
                "name": "f",
                "output": False,
                "str": "File",
            },
            "of": {
                "path_type": "file",
                "is_path": True,
                "is_directory": False,
                "is_file": True,
                "list": False,
                "name": "of",
                "output": True,
                "str": "File",
            },
            "lf": {
                "path_type": "file",
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "lf",
                "output": False,
                "str": "List[File]",
            },
            "olf": {
                "path_type": "file",
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "olf",
                "output": True,
                "str": "List[File]",
            },
            "d": {
                "path_type": "directory",
                "is_path": True,
                "is_directory": True,
                "is_file": False,
                "list": False,
                "name": "d",
                "output": False,
                "str": "Directory",
            },
            "od": {
                "path_type": "directory",
                "is_path": True,
                "is_directory": True,
                "is_file": False,
                "list": False,
                "name": "od",
                "output": True,
                "str": "Directory",
            },
            "ld": {
                "path_type": "directory",
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "ld",
                "output": False,
                "str": "List[Directory]",
            },
            "old": {
                "path_type": "directory",
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "old",
                "output": True,
                "str": "List[Directory]",
            },
            "u": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "u",
                "output": False,
                "str": "Union[str,List[str]]",
            },
            "ou": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "ou",
                "output": True,
                "str": "Union[str,List[str]]",
            },
            "lu": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "lu",
                "output": False,
                "str": "List[Union[str,List[str]]]",
            },
            "olu": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "olu",
                "output": True,
                "str": "List[Union[str,List[str]]]",
            },
            "m": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "m",
                "output": False,
                "str": "dict",
            },
            "om": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "om",
                "output": True,
                "str": "dict",
            },
            "lm": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "lm",
                "output": False,
                "str": "List[dict]",
            },
            "olm": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "olm",
                "output": True,
                "str": "List[dict]",
            },
            "mt": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "mt",
                "output": False,
                "str": "dict[str,List[int]]",
            },
            "l": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "l",
                "output": False,
                "str": "list",
            },
            "ll": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "ll",
                "output": False,
                "str": "List[List[str]]",
            },
            "c": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "c",
                "output": False,
                "str": "Controller",
            },
            "lc": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "lc",
                "output": False,
                "str": "List[Controller]",
            },
            "o": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "o",
                "output": False,
                "str": f"Controller[{__name__}.SubController]",
            },
            "lo": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": True,
                "name": "lo",
                "output": False,
                "str": f"List[Controller[{__name__}.SubController]]",
            },
            "set": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "set",
                "output": False,
                "str": "set",
            },
            "Set": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "Set",
                "output": False,
                "str": "set",
            },
            "Set_str": {
                "path_type": None,
                "is_path": False,
                "is_directory": False,
                "is_file": False,
                "list": False,
                "name": "Set_str",
                "output": False,
                "str": "set[str]",
            },
        }
        for n, i in d.items():
            self.assertEqual(d[n], expected[n])
        self.assertEqual(len(d), len(expected))

    def test_default_value(self):
        class C(Controller):
            m1: str
            m2: field(type_=str, optional=False)
            m3: field(type_=str, optional=False) = ""
            m4: field(type_=str, default="", optional=False)
            m5: field(type_=list, default_factory=lambda: [], optional=False)
            o1: str = ""
            o2: field(type_=str, optional=True)
            o3: field(type_=str) = ""
            o4: field(type_=str, default="")
            o5: field(type_=list, default_factory=lambda: [])

        o = C()
        d = {
            f.name: {
                "name": f.name,
                "optional": f.optional,
                "has_default": f.has_default(),
            }
            for f in o.fields()
        }
        expected = {
            "m1": {
                "name": "m1",
                "optional": False,
                "has_default": False,
            },
            "m2": {
                "name": "m2",
                "optional": False,
                "has_default": False,
            },
            "m3": {
                "name": "m3",
                "optional": False,
                "has_default": True,
            },
            "m4": {
                "name": "m4",
                "optional": False,
                "has_default": True,
            },
            "m5": {
                "name": "m5",
                "optional": False,
                "has_default": True,
            },
            "o1": {
                "name": "o1",
                "optional": True,
                "has_default": True,
            },
            "o2": {
                "name": "o2",
                "optional": True,
                "has_default": False,
            },
            "o3": {
                "name": "o3",
                "optional": True,
                "has_default": True,
            },
            "o4": {
                "name": "o4",
                "optional": True,
                "has_default": True,
            },
            "o5": {
                "name": "o5",
                "optional": True,
                "has_default": True,
            },
        }
        for n, i in d.items():
            self.assertEqual(d[n], expected[n])
        self.assertEqual(len(d), len(expected))

    def test_instance_default_value(self):
        c = Controller()
        c.add_field("thing", str, 12)
        self.assertEqual(c.thing, "12")
        c.add_field("other", field(type_=int, default=25))
        self.assertEqual(c.other, 25)

    def test_repr(self):
        c = Controller()
        c.add_field("thing", str, 12)
        c.add_field("other", int)
        self.assertEqual(repr(c), "EmptyController(thing='12', other=undefined)")

    def test_add_field(self):
        c = Controller()

        c.add_field("toto", field(type_=str))
        c.toto = "titi"
        self.assertEqual([i.name for i in c.fields()], ["toto"])

    def test_singleton(self):
        class Application(Singleton, Controller):
            pass

        app1 = Application()
        app1.add_field("toto", str)
        app2 = Application()
        self.assertEqual([i.name for i in app2.fields()], ["toto"])

    def test_json(self):
        c1 = SerializableController(
            s="toto",
            i=42,
            n=12.34,
            b=True,
            e="two",
            f="/a_file.txt",
            d="/somewhere",
            u=["one", "two"],
            m={},
            lm=[{}],
            mt={"toto": [1, 2, 3]},
            l=[],
            ll=[["1", "2"], ["a", "b"]],
            # Serialization of derived types is not implemented yet.
            # Here the field type is Controller but the value type
            # is SerializableController.
            # c=SerializableController(
            #     s='toto',
            #     i=42,
            #     n=12.34,
            #     b=True),
            # lc=[Controller(), Controller()],
            o=SubController(dummy="toto"),
            lo=[SubController(dummy="tutu"), SubController(dummy="tata")],
            set_str={"a", "b", "c"},
            set={1, "two", None},
        )
        j = json.dumps(c1.json_controller())
        c2 = SerializableController()
        c2.import_json(json.loads(j))
        self.assertEqual(c1.asdict(), c2.asdict())

    def test_validator(self):
        class C(Controller):
            s: Literal["a", "b"]

            @pydantic.validator("*", pre=True)
            def to_lower(cls, value):
                if isinstance(value, str):
                    return value.lower()
                return value

        o = C(s="A")
        self.assertEqual(o.s, "a")

    def test_field_proxy(self):
        class C(Controller):
            class_file: File
            class_int: int = 32
            class_not_list: File = "/here"

        c = C()
        c.add_field("instance_file", type_=File)
        c.add_field("instance_int", type_=int)
        c.add_field("instance_not_list", type_=File, default="/there")

        ic = Controller()

        ic.add_proxy("c_not_list", c, "class_not_list")
        ic.add_proxy("i_not_list", c, "instance_not_list")
        self.assertEqual(ic.c_not_list, "/here")
        self.assertEqual(ic.field("c_not_list").type, File)
        self.assertEqual(ic.field("c_not_list").path_type, "file")
        self.assertEqual(ic.i_not_list, "/there")
        self.assertEqual(ic.field("i_not_list").type, File)
        self.assertEqual(ic.field("i_not_list").path_type, "file")

        ic.change_proxy("c_not_list", proxy_field="class_int")
        self.assertEqual(ic.c_not_list, 32)
        self.assertEqual(ic.field("c_not_list").type, int)
        self.assertEqual(ic.field("c_not_list").path_type, None)

        ic.add_list_proxy("class_files", c, "class_file")
        ic.add_list_proxy("instance_files", c, "instance_file")
        ic.add_list_proxy("list_changing", c, "class_int")

        self.assertEqual(ic.field("class_files").type, list[File])
        self.assertEqual(ic.field("class_files").path_type, "file")
        self.assertEqual(ic.field("instance_files").type, list[File])
        self.assertEqual(ic.field("instance_files").path_type, "file")

        self.assertEqual(ic.field("list_changing").type, list[int])
        self.assertEqual(ic.field("list_changing").path_type, None)
        with self.assertRaises(pydantic.ValidationError):
            ic.list_changing = ["/a", "/b", "/c"]
        ic.list_changing = [1, 2, 3]

        ic.change_proxy("list_changing", proxy_field="class_file")
        self.assertEqual(ic.field("list_changing").type, list[File])
        self.assertEqual(ic.field("list_changing").path_type, "file")
        # self.assertEqual(ic.list_changing, ['1', '2', '3'])
        ic.list_changing = ["/a", "/b", "/c"]

        ic.change_proxy("list_changing", proxy_field="instance_int")
        self.assertEqual(ic.field("list_changing").type, list[int])
        self.assertEqual(ic.field("list_changing").path_type, None)

        ic.change_proxy("list_changing", proxy_field="instance_file")
        self.assertEqual(ic.field("list_changing").type, list[File])
        self.assertEqual(ic.field("list_changing").path_type, "file")


def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestController)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    unittest.main()
