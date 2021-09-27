# -*- coding: utf-8 -*-

from typing import List
import unittest

from soma.controller import controller, Controller, field, open_key_controller, OpenKeyController
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
        @controller
        class Zuzur:
            glop: str = 'zut'

        c2 = Zuzur()
        c3 = Zuzur()
        self.assertEqual(c2.glop, 'zut')
        c2.glop = 'I am c2'
        c3.glop = 'I am c3'
        self.assertEqual(c2.glop, 'I am c2')
        self.assertEqual(c3.glop, 'I am c3')

    def test_controller3(self):
        @controller
        class Babar:
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
        @controller
        class Driver:
            head : str = ''
            arms : str = ''
            legs : str = ''

        @controller
        class Car:
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

        #TODO:
        manhelp = get_trait_desc('driver', my_car.trait('driver'))
        self.assertEqual(
            manhelp[0],
            "driver: a legal value (['ControllerTrait'] - mandatory)")
        self.assertEqual(manhelp[1], "    the guy who would better take a bus")

    def test_dynamic_controllers(self):
        # New API forbid derivation of Controller class
        self.assertRaises(TypeError, type, 'MyClass', (Controller,), {})

        @controller
        class C:
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
        @open_key_controller(value_type=OpenKeyController)
        class ControllerOfController:
            static : str = 'present'
        
        o = ControllerOfController()
        o.new_controller = {'first': 1,
                            'second': 'two'}
        self.assertEqual([i.name for i in o.fields()], ['static', 'new_controller'])
        self.assertEqual(o.new_controller.asdict(), {'first': '1', 'second': 'two'})
    
    
    # def test_trait_utils1(self):
    #     """ Method to test if we can build a string description for a trait.
    #     """
    #     #TODO: redefine how to add attributes to traits
    #     trait = traits.CTrait(0)
    #     trait.handler = traits.Float()
    #     trait.ouptut = False
    #     trait.optional = True
    #     trait.desc = "bla"
    #     manhelp = get_trait_desc("float_trait", trait, 5)
    #     self.assertEqual(
    #         manhelp[0],
    #         "float_trait: a float (['Float'] - optional, default value: 5)")
    #     self.assertEqual(manhelp[1], "    bla")

    # def test_trait_utils2(self):
    #     trait = traits.CTrait(0)
    #     trait.handler = traits.Float()
    #     trait.ouptut = True
    #     trait.optional = False
    #     manhelp = get_trait_desc("float_trait", trait, 5)
    #     self.assertEqual(
    #         manhelp[0],
    #         "float_trait: a float (['Float'] - mandatory, default value: 5)")
    #     self.assertEqual(manhelp[1], "    No description.")

    # def test_trait_utils3(self):
    #     class Blop(object):
    #         pass
    #     trait = traits.CTrait(0)
    #     trait.handler = traits.Instance(Blop())
    #     trait.ouptut = False
    #     trait.optional = False
    #     manhelp = get_trait_desc("blop", trait, None)
    #     desc = ' '.join([x.strip() for x in manhelp[:-1]])
    #     self.assertEqual(
    #         desc,
    #         "blop: a Blop or None (['Instance_%s.Blop'] - mandatory)"
    #         % Blop.__module__)
    #     self.assertEqual(manhelp[-1], "    No description.")

    # def test_trait_utils4(self):
    #     trait = traits.Either(traits.Int(47), traits.Str("vovo")).as_ctrait()
    #     trait.ouptut = False
    #     trait.optional = False
    #     manhelp = get_trait_desc("choice", trait, None)
    #     desc = ' '.join([x.strip() for x in manhelp[:-1]])
    #     self.assertTrue(
    #         desc in ("choice: an integer (int or long) or a string "
    #                  "(['Int', 'Str'] - mandatory)",
    #                  "choice: an integer or a string "
    #                  "(['Int', 'Str'] - mandatory)"))
    #     self.assertEqual(manhelp[-1], "    No description.")


    # def test_trait(self):
    #     """ Method to test trait characterisitics: value, type.
    #     """
    #     self.assertTrue(is_trait_value_defined(5))
    #     self.assertFalse(is_trait_value_defined(""))
    #     self.assertFalse(is_trait_value_defined(None))
    #     self.assertFalse(is_trait_value_defined(traits.Undefined))

    #     trait = traits.CTrait(0)
    #     trait.handler = traits.Float()
    #     self.assertFalse(is_trait_pathname(trait))
    #     for handler in [traits.File(), traits.Directory()]:
    #         trait.handler = handler
    #         self.assertTrue(is_trait_pathname(trait))




def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestController)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
