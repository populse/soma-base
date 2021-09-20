# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
from typing import List
import unittest

from soma.controller import Controller, OpenKeyController
from soma.undefined import undefined


class TestController(unittest.TestCase):

#     def test_controller(self):
#         c1 = Controller()
#         c1.add_trait('gogo', str)
#         c1.add_trait('bozo', int, 12)
#         #TODO: change test to undefined c1.gogo value ?
#         self.assertEqual(c1.gogo, '')
#         self.assertEqual(c1.bozo, 12)
#         self.assertEqual(list(c1.user_traits().keys()), ['gogo', 'bozo'])
#         c1.gogo = 'blop krok'
#         self.assertEqual(c1.gogo, 'blop krok')
#         d = c1.export_to_dict()
#         self.assertEqual(d, {'gogo': 'blop krok', 'bozo': 12})
#         c1.reorder_traits(['bozo', 'gogo'])
#         self.assertEqual(list(c1.user_traits().keys()), ['bozo', 'gogo'])
#         c1.reorder_traits(['gogo', 'bozo'])
#         self.assertEqual(list(c1.user_traits().keys()), ['gogo', 'bozo'])

#     def test_controller2(self):
#         class Zuzur(Controller):
#             glop: str = 'zut'

#         c2 = Zuzur()
#         c3 = Zuzur()
#         self.assertEqual(c2.glop, 'zut')
#         c2.glop = 'I am c2'
#         c3.glop = 'I am c3'
#         self.assertEqual(c2.glop, 'I am c2')
#         self.assertEqual(c3.glop, 'I am c3')

#     def test_controller3(self):
#         class Babar(Controller):
#             hupdahup: str = 'barbatruc'
#             gargamel: str
#             ouioui: List[str]

#         c1 = Babar()
#         #TODO: change test for AttributeError
#         self.assertEqual(c1.gargamel, traits.Undefined)
#         d = c1.export_to_dict()
#         #TODO: change test for 'gargame1' no in dict
#         self.assertEqual(d, {'hupdahup': 'barbatruc',
#                              'gargamel': traits.Undefined,
#                              'ouioui': []})
#         c2 = Babar()
#         c2.gargamel = 'schtroumpf'
#         c2.import_from_dict(d)
#         self.assertEqual(c2.export_to_dict(), d)
#         d = c1.export_to_dict(exclude_undefined=True)
#         self.assertEqual(d, {'hupdahup': 'barbatruc', 'ouioui': []})
#         c2.gargamel = 'schtroumpf'
#         c2.import_from_dict(d)
#         self.assertEqual(c2.export_to_dict(exclude_empty=True),
#                          {'hupdahup': 'barbatruc', 'gargamel': 'schtroumpf'})

#     def test_controller4(self):
#         class Driver(Controller):
#             head : str
#             arms : str
#             legs : str

#         class Car(Controller):
#             wheels : str
#             engine : str
#             driver : Driver = Driver()
# #                                     desc='the guy who would better take a '
# #                                     'bus')
#             problems = OpenKeyController(str)

#         my_car = Car()
#         my_car.wheels = 'flat'
#         my_car.engine = 'wind-broken'
#         my_car.driver.head = 'empty'
#         my_car.driver.arms = 'heavy'
#         my_car.driver.legs = 'short'
#         my_car.problems = {'exhaust': 'smoking', 'windshield': 'cracked'}

#         d = my_car.export_to_dict()
#         self.assertEqual(d, {'wheels': 'flat', 'engine': 'wind-broken',
#                              'driver': {'head': 'empty', 'arms': 'heavy',
#                                         'legs': 'short'},
#                              'problems': {'exhaust': 'smoking',
#                                           'windshield': 'cracked'}})
#         self.assertTrue(isinstance(my_car.driver, Driver))
#         self.assertTrue(isinstance(my_car.problems, OpenKeyController))
#         my_car.driver = {'head': 'smiling', 'legs': 'strong'}
#         d = my_car.export_to_dict()
#         self.assertEqual(d, {'wheels': 'flat', 'engine': 'wind-broken',
#                              'driver': {'head': 'smiling', 'arms': '',
#                                         'legs': 'strong'},
#                              'problems': {'exhaust': 'smoking',
#                                           'windshield': 'cracked'}})

#         other_car = my_car.copy(with_values=True)
#         self.assertEqual(other_car.export_to_dict(), d)
#         other_car = my_car.copy(with_values=False)
#         #TODO: check appropriate behavior
#         self.assertEqual(other_car.export_to_dict(),
#                          {'wheels': '', 'engine': '',
#                           'driver': {'head': 'empty', 'arms': 'heavy',
#                                      'legs': 'short'},
#                           'problems': {}})

#         #TODO: change exception type
#         self.assertRaises(traits.TraitError,
#                           setattr, my_car.problems, 'fuel', 3.5)
#         del my_car.problems.fuel
#         self.assertEqual(sorted(my_car.problems.user_traits().keys()),
#                          ['exhaust', 'windshield'])

#         #TODO:
#         manhelp = get_trait_desc('driver', my_car.trait('driver'))
#         self.assertEqual(
#             manhelp[0],
#             "driver: a legal value (['ControllerTrait'] - mandatory)")
#         self.assertEqual(manhelp[1], "    the guy who would better take a bus")

    def test_dynamic_controllers(self):
        class C(Controller):
            static_int : int = 0
            static_str : str
            static_list: list = []
            static_dict: dict = {}

        o = C(static_str='')

        o.add_trait('dynamic_int', int, default=0)
        o.add_trait('dynamic_str', str, default='default', custom_attribute=True)
        o.add_trait('dynamic_list', List[int])
        self.assertEqual(o.traits['dynamic_str'].custom_attribute, True)

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
            ['x', undefined], 
            ['x', undefined, 'dynamic_str'],
            ['x', undefined, 'dynamic_str', o],
            ])
        self.assertEqual(o.traits['dynamic_int'].__dict__, {
            'alias': None,
            'class_trait': False,
            'default': 0,
            'name': 'dynamic_int',
            'required': False,
            'type_': int})
        self.assertEqual(o.traits['dynamic_str'].__dict__, {
            'alias': None,
            'class_trait': False,
            'default': 'default',
            'name': 'dynamic_str',
            'required': False,
            'custom_attribute': True,
            'type_': str})
        self.assertEqual(o.traits['static_dict'].__dict__, {
            'alias': 'static_dict',
            'class_trait': True,
            'default': {},
            'name': 'static_dict',
            'required': False,
            'type_': dict})
        self.assertEqual(o.traits['static_list'].__dict__, {
            'alias': 'static_list',
            'class_trait': True,
            'default': [],
            'name': 'static_list',
            'required': False,
            'type_': list})
        self.assertEqual(o.traits['dynamic_list'].__dict__, {
            'alias': None,
            'class_trait': False,
            'default': undefined,
            'name': 'dynamic_list',
            'required': True,
            'type_': List[int]})


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
