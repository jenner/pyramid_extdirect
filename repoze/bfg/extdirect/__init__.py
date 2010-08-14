from zope.interface import Interface, implements
from zope.configuration.fields import GlobalObject
from zope.schema import TextLine
from zope.schema import Bool

from repoze.bfg.zcml import route, utility
from repoze.bfg.configuration import Configurator
from repoze.bfg.threadlocal import get_current_registry
from repoze.bfg.path import caller_package

from repoze.bfg.compat import json
from repoze.bfg.security import has_permission

from webob import Response
from cStringIO import StringIO
import sys, traceback
import inspect
import venusian

# form parameters sent by ExtDirect when using a form-submit
# see http://www.sencha.com/products/js/direct.php
FORM_DATA_KEYS = (
    "extAction",
    "extMethod",
    "extTID",
    "extUpload",
    "extType"
)

# response to a file upload cannot be return as application/json, ExtDirect defines
# a special html response body for this use case where the response data is
# added to a textarea for faster JS-side decoding (since etxtarea text is not a DOM node)
FORM_SUBMIT_RESPONSE_TPL = '<html><body><textarea>%s</textarea></body></html>'

def _mk_cb_key(action_name, method_name):
    return action_name + '#' + method_name

class JsonReprEncoder(json.JSONEncoder):
    """ a convenience wrapper for classes that support json_repr() """
    def default(self, obj):
        jr = getattr(obj, 'json_repr', None)
        if jr is None:
            return super(PtEncoder, self).default(obj)
        return jr()

class IExtdirect(Interface):
    """ marker iface for Extdirect utility """
    pass


class Extdirect(object):
    """
        Handles ExtDirect API respresentation and routing.
        
        The Extdirect accepts a number of arguments: ``app``,
        ``api_path``, ``router_path``, ``namespace``, ``descriptor``
        and ``expose_exceptions``.

        The ``app`` argument is a python package or module used
        which is used to scan for ``extdirect_method`` decorated
        functions/methods once the API is built.

        The ``api_path`` and ``router_path`` arguments are the
        paths/URIs of repoze.bfg views. ``api_path`` renders
        the ExtDirect API, ``router_path`` is the routing endpoint
        for ExtDirect calls.

        If the ``namespace`` argument is passed it will be used in
        the API as Ext namespace (default is 'Ext.app').

        If the ``descriptor`` argument is passed it's used as ExtDirect
        API descriptor name (default is Ext.app.REMOTING_API).

        See http://www.sencha.com/products/js/direct.php for further infos.
        
        The optional ``expose_exceptions`` argument controls the output of
        an ExtDirect call - if ``True``, the router will provide additional
        information about exceptions.
    """

    implements(Interface)

    venusian = venusian

    def __init__(self, app, api_path, router_path, namespace='Ext.app', descriptor='Ext.app.REMOTING_API', expose_exceptions=True):
        self.app = app
        self.api_path = api_path
        self.router_path = router_path
        self.namespace = namespace
        self.descriptor = descriptor
        self.expose_exceptions = expose_exceptions

        self.actions = {}

        self.scanned = False

    def add_action(self, action_name, **settings):
        """
            Registers an action.
            
            ``action_name``: Action name

            Possible values of `settings``:

            ``method_name``: Method name
            ``callback``: The callback to execute upon client request
            ``numargs``: Number of arguments passed to the wrapped callable
            ``scope``: class/module/exec/etc., see venusian.advice.getFrameInfo()
            ``accept_files``: If true, this action will be declared as formHandler in API
            ``instance_name``: In case we're dealing with an instance method ``instance_name``
                is the name of the traversable object in BFG traversal graph
            ``permission``: The permission needed to execute the wrapped callable
            ``request_as_last_param``: If true, the wrapped callable will receive a request object
                as last argument

            """
        if action_name not in self.actions:
            self.actions[action_name] = {}
        self.actions[action_name][_mk_cb_key(action_name, settings['method_name'])] = settings

    def get_actions(self):
        """ build and return a dict of actions to be used in ExtDirect API """
        ret = {}
        for k, v in self.actions.items():
            itms = []
            for settings in v.values():
                d = dict(
                    len = settings['numargs'],
                    name = settings['method_name']
                )
                if settings['accepts_files']:
                    d['formHandler'] = True
                itms.append(d)
            ret[k] = itms
        return ret

    def get_method(self, action, method):
        """ returns a method's settings """
        if action not in self.actions:
            raise KeyError("Invalid action: " + action)
        key = _mk_cb_key(action, method)
        if not key in self.actions[action]:
            raise KeyError("No such method in '%s': '%s':" % (action, method))
        return self.actions[action][key]

    def _assert_scanned(self):
        """ scans the venusian decorator for our package/module """
        if not self.scanned:
            scanner = self.venusian.Scanner(extdirect=self)
            scanner.scan(self.app, categories=['extdirect'])
            self.scanned = True

    def dump_api(self, request):
        """ dump all known remote methods """
        self._assert_scanned()
        ret = ["Ext.ns('%s'); %s = " % (self.namespace, self.descriptor)]
        apidict = dict(
            url = request.application_url + '/' + self.router_path,
            type = 'remoting',
            namespace = self.namespace,
            actions = self.get_actions()
        )
        ret.append(json.dumps(apidict))
        ret.append(";")
        return "".join(ret)

    def _do_route(self, action_name, method_name, params, transaction_id, request):
        """ performs routing, i.e. calls decorated methods/functions """
        settings = self.get_method(action_name, method_name)
        permission = settings.get('permission', None)
        ret = {
            "type": "rpc",
            "tid": transaction_id,
            "action": action_name,
            "method": method_name,
            "result": None
        }
        req_as_last = settings.get('request_as_last_param', False)
        if params is None:
            params = list()
        if req_as_last:
            params = params + [request]
        try:
            callback = settings['callback']
            if settings['scope'] == 'class':
                # FIXME this relies heavily on BFGs model traversal
                instance = request.root[settings['instance_name']]
                if permission is not None and not has_permission(permission, instance, request):
                    raise Exception("Access denied")
                params = [instance] + params
                if callback is None or not callable(callback):
                    raise Exception("Invalid method '%s' for action '%s'" % (method_name, action_name,))
            if params:
                result = callback(*params)
            else:
                result = callback()

            ret["result"] = result
        except Exception, e:
            ret["type"] = "exception"
            if self.expose_exceptions:
                f = StringIO()
                traceback.print_exc(file=f)
                ret["result"] = {'error': True, 'message': str(e), 'exception_class': str(Exception), 'stacktrace': f.getvalue()}
            else:
                ret["result"] = {'error': True, 'message': 'Error executing %s.%s' % (action_name, method_name,)}
        return ret

    def route(self, request):
        self._assert_scanned()
        is_form_data = False
        if is_form_submit(request):
            is_form_data = True
            params = parse_extdirect_form_submit(request)
        else:
            params = parse_extdirect_request(request)
        ret = []
        for (act, meth, params, tid) in params:
            ret.append(self._do_route(act, meth, params, tid, request))
        if not is_form_data:
            if len(ret) == 1:
                ret = ret[0]
            return (json.dumps(ret, cls=JsonReprEncoder), False)
        ret = ret[0] # form data cannot be batched
        s = json.dumps(ret, cls=JsonReprEncoder).replace('&quot;', '\\&quot;')
        return (FORM_SUBMIT_RESPONSE_TPL % (s,), True)


class extdirect_method(object):
    """ enables direct extjs access to python methods through json/form submit """

    venusian = venusian # for testing injection
    def __init__(self, action=None, method_name=None, permission=None, accepts_files=False, request_as_last_param=False):
        self.action = action
        self.method_name = method_name
        self.permission = permission
        self.accepts_files = accepts_files
        self.request_as_last_param = request_as_last_param

    def __call__(self, wrapped):
        args, varargs, varkw, defaults = inspect.getargspec(wrapped)

        numargs = len(args)

        settings = self.__dict__.copy()

        def callback(scanner, name, ob):
            if self.action is not None:
                name = self.action
            elif settings['scope'] == 'class':
                extdirect_settings = getattr(ob, '__extdirect_settings__', None)
                if extdirect_settings is not None:
                    if 'default_action_name' in extdirect_settings:
                        name = extdirect_settings['default_action_name']
                    if self.permission is None and 'default_permission' in extdirect_settings:
                        settings['permission'] = extdirect_settings['default_permission']
            if 'action' in settings:
                del settings['action']

            scanner.extdirect.add_action(name, callback=wrapped, numargs=numargs, **settings)

        info = self.venusian.attach(wrapped, callback, category='extdirect')

        settings['scope'] = info.scope
        if info.scope == 'class':
            numargs = numargs - 1
            if '__acl__' in info.locals:
                settings['acl'] = info.locals['__acl__']
            if settings.get('method_name', None) is None:
                settings['method_name'] = wrapped.__name__
            settings['instance_name'] = None
            if '__name__' in info.locals:
                settings['instance_name'] = info.locals['__name__']
        elif info.scope == 'module':
            if settings.get('method_name', None) is None:
                settings['method_name'] = wrapped.func_name

        return wrapped

def is_form_submit(request):
    """ checks if a request contains extdirect form submit """
    p = request.params
    keys = list(FORM_DATA_KEYS)
    for key in p.keys():
        if key in keys:
            keys.remove(key)
    return len(keys) == 0

def parse_extdirect_form_submit(request):
    """
        Extracts extdirect remoting parameters from request
        which are provided by a form submission
    """
    p = request.params
    if not p:
        raise Exception("Could not parse form submit")
    action = p.get('extAction')
    method = p.get('extMethod')
    tid = p.get('extTID')
    data = {}
    for key in p.keys():
        if key in FORM_DATA_KEYS:
            continue
        data[key] = p.get(key)
    return [(action, method, [data], tid)]

def parse_extdirect_request(request):
    """ 
        Extracts extdirect remoting parameters from request
        which are provided by an AJAX request
    """
    body = request.body
    decoded_body = json.loads(body)
    ret = []
    if type(decoded_body) is not list:
        decoded_body = [decoded_body]
    for p in decoded_body:
        action = p['action']
        method = p['method']
        data = p['data']
        tid = p['tid']
        ret.append((action, method, data, tid))
    return ret


def api_view(request):
    """ renders the API """
    util = get_current_registry().getUtility(IExtdirect)
    body = util.dump_api(request)
    return Response(body, content_type='text/javascript', charset='UTF-8')

def router_view(request):
    """ renders the result of a ExtDirect call """
    util = get_current_registry().getUtility(IExtdirect)
    (body, is_form_data) = util.route(request)
    ctype = 'application/json'
    if is_form_data:
        ctype = 'text/html'
    return Response(body, content_type=ctype, charset='UTF-8')
