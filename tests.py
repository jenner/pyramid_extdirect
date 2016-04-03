import unittest
from pyramid import testing


class Dummy(object):
    pass


class DummyAjaxRequest(testing.DummyRequest):

    def __init__(self, params=None, environ=None, headers=None, path='/',
            cookies=None, post=None, body='', **kw):
        super(DummyAjaxRequest, self).__init__(params, environ, headers, path,
                cookies, post, **kw)
        self.body = body

class TestPyramidExtDirect(unittest.TestCase):

    def setUp(self):
        from pyramid_extdirect import includeme
        self.config = testing.setUp()
        includeme(self.config)
        self.config.end()

    def tearDown(self):
        testing.tearDown()

    def _get_util(self):
        from pyramid_extdirect import IExtdirect
        return self.config.registry.getUtility(IExtdirect)

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

    def test_register_class_method(self):
        from pyramid_extdirect import IExtdirect, _mk_cb_key
        action_name = 'MyClass'
        meth_name = 'my_foo'
        dec = self._makeOne(action=action_name)
        class MyClass(object):
            @dec
            def my_foo(self):
                pass
        dec.register(self, meth_name, MyClass)

        extdirect = self.config.registry.getUtility(IExtdirect)
        key = _mk_cb_key(action_name, meth_name)

        self.assertEqual(extdirect.actions[action_name][key]['class'], MyClass)
        self.assertEqual(dec._settings["original_name"], meth_name)
        self.assertEqual(dec._settings["action"], action_name)

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

    def test_request_as_last_param(self):
        dec = self._makeOne(action='FooAction', request_as_last_param=True)
        def foo(request): pass
        decorated = dec(foo)
        dec.register(self, 'foo', foo)

        util = self._get_util()
        api_desc = util.get_actions()['FooAction'][0]
        self.assertEqual(api_desc['len'], 0)

    def test_simple_call(self):
        dec = self._makeOne(action='SimpleAction')
        def foo(param):
            return param + ' was handled'
        decorated = dec(foo)
        dec.register(self, 'foo', foo)

        util = self._get_util()
        body = b"""{"action": "SimpleAction", "method": "foo", "data":["sample request"], "tid":0}"""
        request = DummyAjaxRequest(body=body)
        response, is_form_data = util.route(request)
        self.failUnless('sample request was handled' in response)
        self.failUnless(not is_form_data)

    def test_simple_call_wo_params(self):
        dec = self._makeOne(action='SimpleAction')
        def foo():
            return 'Heya!'
        decorated = dec(foo)
        dec.register(self, 'foo', foo)

        util = self._get_util()
        body = b"""{"action": "SimpleAction", "method": "foo", "data":null, "tid":0}"""
        request = DummyAjaxRequest(body=body)
        response, is_form_data = util.route(request)
        self.failUnless('Heya!' in response)

    def test_invalid_action(self):
        dec = self._makeOne(action='SimpleAction')
        def foo(param):
            return param + ' was handled'
        decorated = dec(foo)
        dec.register(self, 'foo', foo)

        util = self._get_util()
        body = b"""{"action": "BogusAction", "method": "foo", "data":["sample request"], "tid":0}"""
        request = DummyAjaxRequest(body=body)
        self.assertRaisesRegexp(KeyError, "Invalid action: BogusAction", util.route, request)

    def test_invalid_method(self):
        dec = self._makeOne(action='SimpleAction')
        def foo(param):
            return param + ' was handled'
        decorated = dec(foo)
        dec.register(self, 'foo', foo)

        util = self._get_util()
        body = b"""{"action": "SimpleAction", "method": "bar", "data":["sample request"], "tid":0}"""
        request = DummyAjaxRequest(body=body)
        self.assertRaisesRegexp(
            KeyError,
            "No such method in 'SimpleAction': 'bar'",
            util.route,
            request)

    def test_file_upload(self):
        dec = self._makeOne(action='SimpleUpload', accepts_files=True)
        def do_upload(upload_data):
            return {'success': True}
        decorated = dec(do_upload)
        dec.register(self, 'do_upload', do_upload)

        util = self._get_util()
        dummy_file = Dummy()
        params = dict(
            extAction='SimpleUpload',
            extMethod='do_upload',
            extTID='0',
            extUpload='1',
            extType='foo',
        )
        post = dict(uploadedFile=dummy_file)
        request = testing.DummyRequest(params=params, post=post)
        (response, is_form_data) = util.route(request)
        self.failUnless(is_form_data)
        self.failUnless('"result": {"success": true}' in response)

    def test_extdirect_js_api(self):
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
        request = testing.DummyRequest()
        result = util.dump_api(request)
        self.assertIn('var Ext = Ext || {};\n', result)
        self.assertIn('Ext.ns(\'Ext.app\'); Ext.app.REMOTING_API = {"url": "http://example.com/extdirect-router", "namespace": "Ext.app", "type": "remoting", "actions":', result)
        self.assertIn('"MyAction": [{"name": "my_foo", "len": 1}]', result)
        self.assertIn('"OtherAction": [{"name": "bar", "len": 2}]', result)
        self.assertIn('"UploadAction": [{"formHandler": true, "name": "upload", "len": 1}]}', result)

    def test_extdirect_js_api_w_actions(self):
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

        util = self._get_util()
        request = testing.DummyRequest(params={'actions': 'OtherAction'})
        result = util.dump_api(request)
        self.assertNotIn('"MyAction": [{"name": "my_foo", "len": 1}]', result)
        self.assertIn('"OtherAction": [{"name": "bar", "len": 2}]', result)
        self.assertNotIn('"UploadAction": [{"formHandler": true, "name": "upload", "len": 1}]}', result)
