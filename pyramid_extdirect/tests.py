import unittest
from pyramid import testing


class TestPyramidExtDirect(unittest.TestCase):

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
        dec = self._makeOne(action='MyAction')
        class MyClass(object):
            @dec
            def my_foo(self):
                pass
        dec.register(self, 'my_foo', MyClass.my_foo)
        self.assertEqual(dec._settings["original_name"], 'my_foo')
        self.assertEqual(dec._settings["action"], 'MyAction')

    def test_api_dict(self):
        dec = self._makeOne(action='MyAction')
        class MyClass(object):
            @dec
            def my_foo(self):
                pass
        dec.register(self, 'my_foo', MyClass.my_foo)

        dec2 = self._makeOne(action='OtherAction')
        def bar(one, two): pass
        decorated_bar = dec2(bar)
        dec2.register(self, 'bar', bar)

        dec3 = self._makeOne(action='UploadAction', accepts_files=True)
        def upload(form): pass
        decorated_upload = dec3(upload)
        dec3.register(self, 'upload', upload)

        util = self._get_util()
        acts_dict = util.get_actions()

        expected = [{'name': 'my_foo', 'len': 1}]
        self.assertEqual(acts_dict['MyAction'], expected)

        expected = [{'name': 'bar', 'len': 2}]
        self.assertEqual(acts_dict['OtherAction'], expected)

        expected = [{'name': 'upload', 'len': 1, 'formHandler': True}]
        self.assertEqual(acts_dict['UploadAction'], expected)
