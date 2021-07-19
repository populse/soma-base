# -*- coding: utf-8 -*-

from __future__ import print_function

from __future__ import absolute_import
import unittest
import shutil
import os
import tempfile
from soma.controller import Controller, ControllerTrait, OpenKeyController
import traits.api as traits
from soma.controller.trait_utils import (
    get_trait_desc, is_trait_value_defined, is_trait_pathname,
    trait_ids)
from soma.controller import factory



class TestController(unittest.TestCase):

    def test_controller(self):
        c1 = Controller()
        c1.add_trait('gogo', traits.Str())
        c1.add_trait('bozo', traits.Int(12))
        self.assertEqual(c1.gogo, '')
        self.assertEqual(c1.bozo, 12)
        self.assertEqual(list(c1.user_traits().keys()), ['gogo', 'bozo'])
        c1.gogo = 'blop krok'
        self.assertEqual(c1.gogo, 'blop krok')
        d = c1.export_to_dict()
        self.assertEqual(d, {'gogo': 'blop krok', 'bozo': 12})
        c1.reorder_traits(['bozo', 'gogo'])
        self.assertEqual(list(c1.user_traits().keys()), ['bozo', 'gogo'])
        c1.reorder_traits(['gogo', 'bozo'])
        self.assertEqual(list(c1.user_traits().keys()), ['gogo', 'bozo'])

    def test_controller2(self):
        class Zuzur(Controller):
            glop = traits.Str('zut')

        c2 = Zuzur()
        c3 = Zuzur()
        self.assertEqual(c2.glop, 'zut')
        c2.glop = 'I am c2'
        c3.glop = 'I am c3'
        self.assertEqual(c2.glop, 'I am c2')
        self.assertEqual(c3.glop, 'I am c3')

    def test_controller3(self):
        class Babar(Controller):
            hupdahup = traits.Str('barbatruc')
            gargamel = traits.Str(traits.Undefined)
            ouioui = traits.List(traits.Str())

        c1 = Babar()
        self.assertEqual(c1.gargamel, traits.Undefined)
        d = c1.export_to_dict()
        self.assertEqual(d, {'hupdahup': 'barbatruc',
                             'gargamel': traits.Undefined,
                             'ouioui': []})
        c2 = Babar()
        c2.gargamel = 'schtroumpf'
        c2.import_from_dict(d)
        self.assertEqual(c2.export_to_dict(), d)
        d = c1.export_to_dict(exclude_undefined=True)
        self.assertEqual(d, {'hupdahup': 'barbatruc', 'ouioui': []})
        c2.gargamel = 'schtroumpf'
        c2.import_from_dict(d)
        self.assertEqual(c2.export_to_dict(exclude_empty=True),
                         {'hupdahup': 'barbatruc', 'gargamel': 'schtroumpf'})

    def test_controller4(self):
        class Driver(Controller):
            head = traits.Str()
            arms = traits.Str()
            legs = traits.Str()

        class Car(Controller):
            wheels = traits.Str()
            engine = traits.Str()
            driver = ControllerTrait(Driver(),
                                     desc='the guy who would better take a '
                                     'bus')
            problems = ControllerTrait(OpenKeyController(traits.Str()))

        my_car = Car()
        my_car.wheels = 'flat'
        my_car.engine = 'wind-broken'
        my_car.driver.head = 'empty' # ! modify class trait !
        my_car.driver.arms = 'heavy'
        my_car.driver.legs = 'short'
        my_car.problems = {'exhaust': 'smoking', 'windshield': 'cracked'}

        d = my_car.export_to_dict()
        self.assertEqual(d, {'wheels': 'flat', 'engine': 'wind-broken',
                             'driver': {'head': 'empty', 'arms': 'heavy',
                                        'legs': 'short'},
                             'problems': {'exhaust': 'smoking',
                                          'windshield': 'cracked'}})
        self.assertTrue(isinstance(my_car.driver, Driver))
        self.assertTrue(isinstance(my_car.problems, OpenKeyController))
        my_car.driver = {'head': 'smiling', 'legs': 'strong'}
        d = my_car.export_to_dict()
        self.assertEqual(d, {'wheels': 'flat', 'engine': 'wind-broken',
                             'driver': {'head': 'smiling', 'arms': '',
                                        'legs': 'strong'},
                             'problems': {'exhaust': 'smoking',
                                          'windshield': 'cracked'}})

        other_car = my_car.copy(with_values=True)
        self.assertEqual(other_car.export_to_dict(), d)
        other_car = my_car.copy(with_values=False)
        self.assertEqual(other_car.export_to_dict(),
                         {'wheels': '', 'engine': '',
                          'driver': {'head': 'empty', 'arms': 'heavy',
                                     'legs': 'short'},
                          'problems': {}})

        self.assertRaises(traits.TraitError,
                          setattr, my_car.problems, 'fuel', 3.5)
        del my_car.problems.fuel
        self.assertEqual(sorted(my_car.problems.user_traits().keys()),
                         ['exhaust', 'windshield'])

        manhelp = get_trait_desc('driver', my_car.trait('driver'))
        self.assertEqual(
            manhelp[0],
            "driver: a legal value (['ControllerTrait'] - mandatory)")
        self.assertEqual(manhelp[1], "    the guy who would better take a bus")


    def test_trait_utils1(self):
        """ Method to test if we can build a string description for a trait.
        """
        trait = traits.CTrait(0)
        trait.handler = traits.Float()
        trait.ouptut = False
        trait.optional = True
        trait.desc = "bla"
        manhelp = get_trait_desc("float_trait", trait, 5)
        self.assertEqual(
            manhelp[0],
            "float_trait: a float (['Float'] - optional, default value: 5)")
        self.assertEqual(manhelp[1], "    bla")

    def test_trait_utils2(self):
        trait = traits.CTrait(0)
        trait.handler = traits.Float()
        trait.ouptut = True
        trait.optional = False
        manhelp = get_trait_desc("float_trait", trait, 5)
        self.assertEqual(
            manhelp[0],
            "float_trait: a float (['Float'] - mandatory, default value: 5)")
        self.assertEqual(manhelp[1], "    No description.")

    def test_trait_utils3(self):
        class Blop(object):
            pass
        trait = traits.CTrait(0)
        trait.handler = traits.Instance(Blop())
        trait.ouptut = False
        trait.optional = False
        manhelp = get_trait_desc("blop", trait, None)
        desc = ' '.join([x.strip() for x in manhelp[:-1]])
        self.assertEqual(
            desc,
            "blop: a Blop or None (['Instance_%s.Blop'] - mandatory)"
            % Blop.__module__)
        self.assertEqual(manhelp[-1], "    No description.")

    def test_trait_utils4(self):
        trait = traits.Either(traits.Int(47), traits.Str("vovo")).as_ctrait()
        trait.ouptut = False
        trait.optional = False
        manhelp = get_trait_desc("choice", trait, None)
        desc = ' '.join([x.strip() for x in manhelp[:-1]])
        self.assertTrue(
            desc in ("choice: an integer (int or long) or a string "
                     "(['Int', 'Str'] - mandatory)",
                     "choice: an integer or a string "
                     "(['Int', 'Str'] - mandatory)"))
        self.assertEqual(manhelp[-1], "    No description.")


    def test_trait(self):
        """ Method to test trait characterisitics: value, type.
        """
        self.assertTrue(is_trait_value_defined(5))
        self.assertFalse(is_trait_value_defined(""))
        self.assertFalse(is_trait_value_defined(None))
        self.assertFalse(is_trait_value_defined(traits.Undefined))

        trait = traits.CTrait(0)
        trait.handler = traits.Float()
        self.assertFalse(is_trait_pathname(trait))
        for handler in [traits.File(), traits.Directory()]:
            trait.handler = handler
            self.assertTrue(is_trait_pathname(trait))




def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestController)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
