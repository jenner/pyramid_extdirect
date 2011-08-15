import unittest
from pyramid import testing


class TestRegisterPyramidExtDirect(unittest.TestCase):

    def setUp(self):
        from pyramid_extdirect import includeme
        self.config = testing.setUp()
        includeme(self.config)
        self.config.end()

    def _makeOne(self, **options):
        from pyramid_extdirect import extdirect_method
        return extdirect_method(**options)

    def test_register_function_without_action(self):
        dec = self._makeOne()
        def my_foo(self): pass
        decorated = dec(my_foo)
        self.assertRaises(ValueError, dec.register, self, None, my_foo)

    def test_register_function_with_action(self):
        dec = self._makeOne(action='SomeAction')
        def my_foo(self): pass
        decorated = dec(my_foo)
        dec.register(self, 'my_foo', my_foo)
        self.assertEqual(dec._settings["action"], 'SomeAction')

    def _get_util(self):
        from pyramid_extdirect import IExtdirect
        return self.config.registry.getUtility(IExtdirect)

    def test_register_class_method(self):
        from pyramid_extdirect import tests
        dec = self._makeOne(action='MyAction')
        class MyClass(object):
            @dec
            def my_foo(self):
                pass
        my_cls = MyClass()
        dec.register(self, 'my_foo', my_cls.my_foo)
        self.assertEqual(dec._settings["original_name"], 'my_foo')
        self.assertEqual(dec._settings["action"], 'MyAction')

