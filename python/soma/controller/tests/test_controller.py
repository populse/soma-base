# -*- coding: utf-8 -*-

import dataclasses
from typing import List, Union, Literal
import unittest

from soma.controller import (Controller,
                             field,
                             OpenKeyController,
                             field_doc, 
                             Any,
                             List,
                             Literal,
                             Tuple,
                             Union,
                             Dict,
                             file,
                             directory,
                             is_path,
                             is_directory,
                             is_file,
                             is_list,
                             is_output,
                             is_optional,
                             has_default,
                             field_type_str)

from soma.undefined import undefined


class TestController(unittest.TestCase):

    def test_controller(self):
        c1 = Controller()
        c1.add_field('gogo', str)
        c1.add_field('bozo', int, 12)
        self.assertRaises(AttributeError, getattr, c1, 'gogo')
        self.assertEqual(c1.bozo, 12)
        self.assertEqual([i.name for i in c1.fields()], ['gogo', 'bozo'])
        c1.gogo = 'blop krok'
        self.assertEqual(c1.gogo, 'blop krok')
        d = c1.asdict()
        self.assertEqual(d, {'gogo': 'blop krok', 'bozo': 12})
        c1.reorder_fields(['bozo', 'gogo'])
        self.assertEqual([i.name for i in c1.fields()], ['bozo', 'gogo'])
        c1.reorder_fields(['gogo', 'bozo'])
        self.assertEqual([i.name for i in c1.fields()], ['gogo', 'bozo'])

    def test_controller2(self):
        class Zuzur(Controller):
            glop: str = 'zut'

        c2 = Zuzur()
        c3 = Zuzur()
        self.assertEqual(c2.glop, 'zut')
        c2.glop = 'I am c2'
        c3.glop = 'I am c3'
        self.assertEqual(c2.glop, 'I am c2')
        self.assertEqual(c3.glop, 'I am c3')

    def test_controller3(self):
        class Babar(Controller):
            hupdahup: str = 'barbatruc'
            gargamel: str
            ouioui: List[str]
            yes_or_no: Literal['yes', 'no']

        c1 = Babar()
        self.assertRaises(AttributeError, getattr, c1, 'gargamel')
        d = c1.asdict()
        self.assertEqual(d, {'hupdahup': 'barbatruc'})
        c2 = Babar()
        c2.gargamel = 'schtroumpf'
        c2.import_dict(d, clear=True)
        self.assertEqual(c2.asdict(), d)
        c2.gargamel = 'schtroumpf'
        c2.import_dict(d)
        c2.ouioui = []
        self.assertEqual(c2.asdict(exclude_empty=True),
                         {'hupdahup': 'barbatruc', 'gargamel': 'schtroumpf'})
        c1.yes_or_no = 'yes'
        c1.yes_or_no = 'no'
        c1.yes_or_no = undefined
        del c1.yes_or_no
        self.assertRaises(Exception, setattr, c1, 'yes_or_no', 'bad value')

    def test_controller4(self):
        class Driver(Controller):
            head : str = ''
            arms : str = ''
            legs : str = ''

        class Car(Controller):
            wheels : str
            engine : str
            driver : Driver = field(
                default_factory=lambda: Driver(),
                desc='the guy who would better take a bus')
            problems : OpenKeyController

        my_car = Car()
        my_car.wheels = 'flat'
        my_car.engine = 'wind-broken'
        my_car.driver.head = 'empty'
        my_car.driver.arms = 'heavy'
        my_car.driver.legs = 'short'
        my_car.problems = {'exhaust': 'smoking', 'windshield': 'cracked'}
        d = my_car.asdict()
        self.assertEqual(d, {'wheels': 'flat', 'engine': 'wind-broken',
                             'driver': {'head': 'empty', 'arms': 'heavy',
                                        'legs': 'short'},
                             'problems': {'exhaust': 'smoking',
                                          'windshield': 'cracked'}})
        self.assertTrue(isinstance(my_car.driver, Driver))
        self.assertTrue(isinstance(my_car.problems, OpenKeyController))
        my_car.driver = {'head': 'smiling', 'legs': 'strong'}
        d = my_car.asdict()
        self.assertEqual(d, {'wheels': 'flat', 'engine': 'wind-broken',
                             'driver': {'head': 'smiling', 'arms': '',
                                        'legs': 'strong'},
                             'problems': {'exhaust': 'smoking',
                                          'windshield': 'cracked'}})

        other_car = my_car.copy(with_values=True)
        self.assertEqual(other_car.asdict(), d)
        other_car = my_car.copy(with_values=False)
        self.assertEqual(other_car.asdict(),
                         {'driver': {'head': '', 'arms': '',
                                     'legs': ''}})

        my_car.problems.fuel = 3.5
        self.assertEqual(my_car.problems.fuel, '3.5')
        self.assertRaises(ValueError,
                          setattr, my_car.problems, 'fuel', {})
        del my_car.problems.fuel
        self.assertEqual([i.name for i in my_car.problems.fields()],
                         ['exhaust', 'windshield'])

        manhelp = field_doc(my_car.field('driver'))
        self.assertEqual(
            manhelp,
            'driver [__main__.Driver]: the guy who would better take a bus')

    def test_dynamic_controllers(self):
        class C(Controller):
            static_int : int = 0
            static_str : str
            static_list: list = field(default_factory=lambda: [])
            static_dict: dict = field(default_factory=lambda: {})

        o = C(static_str='')

        o.add_field('dynamic_int', int, default=0)
        o.add_field('dynamic_str', str, default='default', custom_attribute=True)
        o.add_field('dynamic_list', List[int])
        self.assertEqual(o.field('dynamic_str').metadata['custom_attribute'], True)

        calls = []
        o.on_attribute_change.add(lambda: calls.append([]))
        o.on_attribute_change.add(lambda one: calls.append([one]))
        o.on_attribute_change.add(lambda one, two: calls.append([one, two]))
        o.on_attribute_change.add(lambda one, two, three: calls.append([one, two, three]))
        o.on_attribute_change.add(lambda one, two, three, four: calls.append([one, two, three, four]))
        self.assertRaises(Exception,
                          o.on_attribute_change.add,
                          lambda one, two, three, four, five:
                            calls.append([one, two, three, four, five]))

        o.static_int = 0
        o.static_int = 42
        o.static_int = 42
        o.anything = 'x'
        self.assertRaises(Exception, setattr, o, 'dynamic_int', 'toto')
        o.dynamic_str = 'x'

        self.assertEqual(calls, [
            [], 
            [42], 
            [42, 0], 
            [42, 0, 'static_int'],
            [42, 0, 'static_int', o],
            [], 
            ['x'], 
            ['x', 'default'], 
            ['x', 'default', 'dynamic_str'],
            ['x', 'default', 'dynamic_str', o],
            ])

        f = o.field('dynamic_int')
        self.assertEqual(f.name, 'dynamic_int')
        self.assertEqual(f.type.__args__[0], int)
        self.assertEqual(f.default, 0)
        self.assertEqual(f.metadata['class_field'], False)
        
        f = o.field('dynamic_str')
        self.assertEqual(f.name, 'dynamic_str')
        self.assertEqual(f.type.__args__[0], str)
        self.assertEqual(f.default, 'default')
        self.assertEqual(f.metadata['class_field'], False)
        self.assertEqual(f.metadata['custom_attribute'], True)

        f = o.field('static_dict')
        self.assertEqual(f.name, 'static_dict')
        self.assertEqual(f.type.__args__[0], dict)
        self.assertEqual(f.default_factory(), {})
        self.assertEqual(f.metadata['class_field'], True)

        f = o.field('static_list')
        self.assertEqual(f.name, 'static_list')
        self.assertEqual(f.type.__args__[0], list)
        self.assertEqual(f.default_factory(), [])
        self.assertEqual(f.metadata['class_field'], True)

        f = o.field('dynamic_list')
        self.assertEqual(f.name, 'dynamic_list')
        self.assertEqual(f.type.__args__[0], List[int])
        self.assertEqual(f.default, undefined)
        self.assertEqual(f.metadata['class_field'], False)


    def test_open_key_controller(self):
        class ControllerOfController(OpenKeyController[OpenKeyController]):
            static : str = 'present'
        
        o = ControllerOfController()
        o.new_controller = {'first': 1,
                            'second': 'two'}
        self.assertEqual(o.static, 'present')
        self.assertEqual([i.name for i in o.fields()], ['static', 'new_controller'])
        self.assertEqual(o.new_controller.asdict(), {'first': '1', 'second': 'two'})
    
    
    def test_field_doc(self):
        f = field(name='float_trait',
                  type_=float,
                  default=5,
                  desc='bla',
                  optional=True,
                  output=True)
        self.assertEqual(
            field_doc(f),
            'float_trait [float] (5): bla')

        f = field(name='float_trait',
                  type_=float,
                  default=5,
                  optional=False,
                  output=True)
        self.assertEqual(
            field_doc(f),
            'float_trait [float] mandatory (5)')

        class Blop(object):
            pass
        f = field(name='blop',
                  type_=Blop,
                  default=None,
                  metadata={
                      'output': False})
        self.assertEqual(
            field_doc(f),
            'blop [{}.Blop] (None)'.format(Blop.__module__))

        f = field(name='choice',
                  type_=Union[str,int],
                  metadata={
                      'output': False})
        self.assertEqual(
            field_doc(f),
            'choice [Union[str,int]] mandatory')

    def test_inheritance(self):
        class Base(Controller):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
            
            base1: str
            base2: str = 'base2'
        
        class Derived(Base):
            derived1: str
            derived2: str = 'derived2'
        
        o = Base()
        o = Derived()
        o.add_field('instance1', str)
        o.add_field('instance2', str, default='instance2')
        self.assertEqual([i.name for i in o.fields()], 
                         ['base1', 'base2', 
                          'derived1', 'derived2',
                          'instance1', 'instance2'])
        self.assertEqual(o.asdict(), 
            {'base2': 'base2', 
             'derived2': 'derived2',
             'instance2': 'instance2'})


    def test_modify_metadata(self):
        class C(Controller):        
            s: field(type_=str,
                     default='',
                     custom='value')
        
        
        o = C()
        o.add_field('d', str, another='value')

        # Metadata of class fields are read-only
        self.assertRaises(TypeError, exec, "o.field('s').metadata['new'] = 'value'",
            locals=locals())
        self.assertRaises(TypeError, exec, "o.field('s').metadata['custom'] = 'modified'",
            locals=locals())
        o.field('d').metadata['new'] = 'value'
        o.field('d').metadata['another'] = 'modified'
        self.assertEqual(o.field('s').metadata, {'class_field': True, 
            'custom': 'value'})
        self.assertEqual(o.field('d').metadata, {'class_field': False, 
            'another': 'modified', 'new': 'value'})


    def test_field_types(self):
        class MyController(Controller):
            dummy : str
        
        class C(Controller):
            s: str
            os: field(type_=str, output=True)
            ls: List[str]
            ols: field(type_=List[str], output=True)

            i: int
            oi: field(type_=int, output=True)
            li: List[int]
            oli: field(type_=List[int], output=True)

            f: float
            of: field(type_=float, output=True)
            lf: List[float]
            olf: field(type_=List[float], output=True)

            b: bool
            ob: field(type_=bool, output=True)
            lb: List[bool]
            olb: field(type_=List[bool], output=True)

            e: Literal['one', 'two', 'three']
            oe: field(type_=Literal['one', 'two', 'three'], output=True)
            le: List[Literal['one', 'two', 'three']]
            ole: field(type_=List[Literal['one', 'two', 'three']], output=True)
            
            f: file()
            of: file(write=True)
            lf: List[file()]
            olf: List[file(write=True)]
            
            d: directory()
            od: directory(write=True)
            ld: List[directory()]
            old: List[directory(write=True)]

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

            o: MyController
            lo: List[MyController]

        o = C()
        d = {
            f.name: {
                'name': f.name,
                'str': field_type_str(f),
                'list': is_list(f),
                'path':is_path(f),
                'file': is_file(f),
                'directory': is_directory(f),
                'output': is_output(f),
            }
            for f in o.fields()
        }
        expected = {
            's': {'directory': False,
                'file': False,
                'list': False,
                'name': 's',
                'output': False,
                'path': False,
                'str': 'str'},
            'os': {'directory': False,
                    'file': False,
                    'list': False,
                    'name': 'os',
                    'output': True,
                    'path': False,
                    'str': 'str'},
            'ls': {'directory': False,
                    'file': False,
                    'list': True,
                    'name': 'ls',
                    'output': False,
                    'path': False,
                    'str': 'list[str]'},
            'ols': {'directory': False,
                    'file': False,
                    'list': True,
                    'name': 'ols',
                    'output': True,
                    'path': False,
                    'str': 'list[str]'},

            'i': {'directory': False,
                'file': False,
                'list': False,
                'name': 'i',
                'output': False,
                'path': False,
                'str': 'int'},
            'oi': {'directory': False,
                    'file': False,
                    'list': False,
                    'name': 'oi',
                    'output': True,
                    'path': False,
                    'str': 'int'},
            'li': {'directory': False,
                    'file': False,
                    'list': True,
                    'name': 'li',
                    'output': False,
                    'path': False,
                    'str': 'list[int]'},
            'oli': {'directory': False,
                    'file': False,
                    'list': True,
                    'name': 'oli',
                    'output': True,
                    'path': False,
                    'str': 'list[int]'},

            'b': {'directory': False,
                'file': False,
                'list': False,
                'name': 'b',
                'output': False,
                'path': False,
                'str': 'bool'},
            'ob': {'directory': False,
                    'file': False,
                    'list': False,
                    'name': 'ob',
                    'output': True,
                    'path': False,
                    'str': 'bool'},
            'lb': {'directory': False,
                    'file': False,
                    'list': True,
                    'name': 'lb',
                    'output': False,
                    'path': False,
                    'str': 'list[bool]'},
            'olb': {'directory': False,
                    'file': False,
                    'list': True,
                    'name': 'olb',
                    'output': True,
                    'path': False,
                    'str': 'list[bool]'},

            'e': {'directory': False,
                'file': False,
                'list': False,
                'name': 'e',
                'output': False,
                'path': False,
                'str': "Literal['one','two','three']"},
            'oe': {'directory': False,
                    'file': False,
                    'list': False,
                    'name': 'oe',
                    'output': True,
                    'path': False,
                    'str': "Literal['one','two','three']"},
            'le': {'directory': False,
                    'file': False,
                    'list': True,
                    'name': 'le',
                    'output': False,
                    'path': False,
                    'str': "list[Literal['one','two','three']]"},
            'ole': {'directory': False,
                    'file': False,
                    'list': True,
                    'name': 'ole',
                    'output': True,
                    'path': False,
                    'str': "list[Literal['one','two','three']]"},

            'f': {'directory': False,
                'file': True,
                'list': False,
                'name': 'f',
                'output': False,
                'path': True,
                'str': 'file'},
            'of': {'directory': False,
                    'file': True,
                    'list': False,
                    'name': 'of',
                    'output': True,
                    'path': True,
                    'str': 'file'},
            'lf': {'directory': False,
                    'file': True,
                    'list': True,
                    'name': 'lf',
                    'output': False,
                    'path': True,
                    'str': 'List[file]'},
            'olf': {'directory': False,
                    'file': True,
                    'list': True,
                    'name': 'olf',
                    'output': True,
                    'path': True,
                    'str': 'List[file]'},

            'd': {'directory': True,
                'file': False,
                'list': False,
                'name': 'd',
                'output': False,
                'path': True,
                'str': 'directory'},
            'od': {'directory': True,
                    'file': False,
                    'list': False,
                    'name': 'od',
                    'output': True,
                    'path': True,
                    'str': 'directory'},
            'ld': {'directory': True,
                    'file': False,
                    'list': True,
                    'name': 'ld',
                    'output': False,
                    'path': True,
                    'str': 'List[directory]'},
            'old': {'directory': True,
                    'file': False,
                    'list': True,
                    'name': 'old',
                    'output': True,
                    'path': True,
                    'str': 'List[directory]'},

            'u': {'directory': False,
                'file': False,
                'list': False,
                'name': 'u',
                'output': False,
                'path': False,
                'str': 'Union[str,list[str]]'},
            'ou': {'directory': False,
                    'file': False,
                    'list': False,
                    'name': 'ou',
                    'output': True,
                    'path': False,
                    'str': 'Union[str,list[str]]'},
            'lu': {'directory': False,
                    'file': False,
                    'list': True,
                    'name': 'lu',
                    'output': False,
                    'path': False,
                    'str': 'list[Union[str,list[str]]]'},
            'olu': {'directory': False,
                    'file': False,
                    'list': True,
                    'name': 'olu',
                    'output': True,
                    'path': False,
                    'str': 'list[Union[str,list[str]]]'},
            
            'm': {'directory': False,
                'file': False,
                'list': False,
                'name': 'm',
                'output': False,
                'path': False,
                'str': 'dict'},
            'om': {'directory': False,
                'file': False,
                'list': False,
                'name': 'om',
                'output': True,
                'path': False,
                'str': 'dict'},
            'lm': {'directory': False,
                'file': False,
                'list': True,
                'name': 'lm',
                'output': False,
                'path': False,
                'str': 'list[dict]'},
            'olm': {'directory': False,
                'file': False,
                'list': True,
                'name': 'olm',
                'output': True,
                'path': False,
                'str': 'list[dict]'},
            
            'mt': {'directory': False,
                'file': False,
                'list': False,
                'name': 'mt',
                'output': False,
                'path': False,
                'str': 'dict[str,list[int]]'},

            'l': {'directory': False,
                'file': False,
                'list': True,
                'name': 'l',
                'output': False,
                'path': False,
                'str': 'list'},
            'll': {'directory': False,
                'file': False,
                'list': True,
                'name': 'll',
                'output': False,
                'path': False,
                'str': 'list[list[str]]'},

            'o': {'directory': False,
                'file': False,
                'list': False,
                'name': 'o',
                'output': False,
                'path': False,
                'str': '__main__.MyController'},
            'lo': {'directory': False,
                'file': False,
                'list': True,
                'name': 'lo',
                'output': False,
                'path': False,
                'str': 'list[__main__.MyController]'},
        }
        for n, i in d.items():
            self.assertEqual(d[n], expected[n])
        self.assertEqual(len(d), len(expected))

    def test_default_value(self):
        class C(Controller):
            m1: str
            m2: field(type_=str, optional=False)
            m3: field(type_=str, optional=False) = ''
            m4: field(type_=str, default='', optional=False)
            m5: field(type_=list, default_factory=lambda: [], optional=False)
            o1: str = ''
            o2: field(type_=str, optional=True)
            o3: field(type_=str) = ''
            o4: field(type_=str, default='')
            o5: field(type_=list, default_factory=lambda: [])

        o = C()
        d = {
            f.name: {
                'name': f.name,
                'optional': is_optional(f),
                'has_default': has_default(f),
            }
            for f in o.fields()
        }
        expected = {
            'm1': {
                'name': 'm1',
                'optional': False,
                'has_default': False,
            },
            'm2': {
                'name': 'm2',
                'optional': False,
                'has_default': False,
            },
            'm3': {
                'name': 'm3',
                'optional': False,
                'has_default': True,
            },
            'm4': {
                'name': 'm4',
                'optional': False,
                'has_default': True,
            },
            'm5': {
                'name': 'm5',
                'optional': False,
                'has_default': True,
            },

            'o1': {
                'name': 'o1',
                'optional': True,
                'has_default': True,
            },
            'o2': {
                'name': 'o2',
                'optional': True,
                'has_default': False,
            },
            'o3': {
                'name': 'o3',
                'optional': True,
                'has_default': True,
            },
            'o4': {
                'name': 'o4',
                'optional': True,
                'has_default': True,
            },
            'o5': {
                'name': 'o5',
                'optional': True,
                'has_default': True,
            },
        }
        for n, i in d.items():
            self.assertEqual(d[n], expected[n])
        self.assertEqual(len(d), len(expected))


if __name__ == "__main__":
    unittest.main()
