
from __future__ import print_function

import unittest
import shutil
import os
import tempfile
from soma.controller import Controller, ControllerTrait, OpenKeyController
import traits.api as traits



class TestController(unittest.TestCase):

    def test_controller(self):
        c1 = Controller()
        c1.add_trait('gogo', traits.Str())
        c1.add_trait('bozo', traits.Int(12))
        self.assertEqual(c1.gogo, '')
        self.assertEqual(c1.bozo, 12)
        self.assertEqual(c1.user_traits().keys(), ['gogo', 'bozo'])
        c1.gogo = 'blop krok'
        self.assertEqual(c1.gogo, 'blop krok')
        d = c1.export_to_dict()
        self.assertEqual(d, {'gogo': 'blop krok', 'bozo': 12})
        c1.reorder_traits(['bozo', 'gogo'])
        self.assertEqual(c1.user_traits().keys(), ['bozo', 'gogo'])
        c1.reorder_traits(['gogo', 'bozo'])
        self.assertEqual(c1.user_traits().keys(), ['gogo', 'bozo'])

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
            driver = ControllerTrait(Driver())
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



def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestController)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()

