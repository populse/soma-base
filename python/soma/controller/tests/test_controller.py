# -*- coding: utf-8 -*-

import dataclasses
from typing import List, Union
import unittest

from soma.controller import (Controller,
                             field,
                             OpenKeyController,
                             field_doc)
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
                metadata={'desc': 'the guy who would better take a bus'})
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
        o.add_field('dynamic_str', str, default='default', metadata=dict(custom_attribute=True))
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
                  metadata={
                      'desc': 'bla',
                      'optional': True,
                      'output': True})
        self.assertEqual(
            field_doc(f),
            'float_trait [float] (5): bla')

        f = field(name='float_trait',
                  type_=float,
                  default=5,
                  metadata={
                      'optional': False,
                      'output': True})
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
                     metadata={'custom': 'value'})
        
        
        o = C()
        o.add_field('d', str, metadata={'another': 'value'})

        o.field('s').metadata['new'] = 'value'
        o.field('s').metadata['custom'] = 'modified'
        o.field('d').metadata['new'] = 'value'
        o.field('d').metadata['another'] = 'modified'
        self.assertEqual(o.field('s').metadata, {'class_field': True, 
            'custom': 'modified', 'new': 'value'})
        self.assertEqual(o.field('d').metadata, {'class_field': False, 
            'another': 'modified', 'new': 'value'})


if __name__ == "__main__":
    unittest.main()
