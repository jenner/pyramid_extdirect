"""
ExtDirect implementation for Pyramid
"""
from collections import defaultdict
import json
import logging
import traceback
try:
    from html.entities import entitydefs  # Python 3
except ImportError:
    from htmlentitydefs import entitydefs  # Python 2

from pyramid.security import has_permission
from pyramid.view import render_view_to_response
from webob import Response
from zope.interface import implementer
from zope.interface import Interface
import venusian

__version__ = '0.5.1'


LOG = logging.getLogger(__name__)

# form parameters sent by ExtDirect when using a form-submit
# see http://www.sencha.com/products/js/direct.php
FORM_DATA_KEYS = frozenset([
    "extAction",
    "extMethod",
    "extMetadata",
    "extTID",
    "extUpload",
    "extType"
])

# response to a file upload cannot be return as application/json, ExtDirect
# defines a special html response body for this use case where the response
# data is added to a textarea for faster JS-side decoding (since textarea text
# is not a DOM node)
FORM_SUBMIT_RESPONSE_TPL = '<html><body><textarea>{}</textarea></body></html>'

JS_API_TPL = """var Ext = Ext || {{}};
Ext.ns('{namespace}'); {descriptor} = {api};
"""


def _mk_cb_key(action_name, method_name):
    """ helper function to create a unique actions dict key """
    return action_name + '#' + method_name


class JsonReprEncoder(json.JSONEncoder):
    """ a convenience wrapper for classes that support json_repr() """
    def default(self, obj):
        if isinstance(obj, Response) and obj.content_type == 'application/json':
            # return decoded response body in case it's an already
            # rendered exception view
            return json.loads(obj.unicode_body)
        json_repr = getattr(obj, 'json_repr', None)
        if json_repr is None:
            return super(JsonReprEncoder, self).default(obj)
        return json_repr()


class IExtdirect(Interface):
    """ marker iface for Extdirect utility """
    pass


class AccessDeniedException(Exception):
    """ marker exception for failed permission checks """
    pass

@implementer(IExtdirect)
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
    paths/URIs of pyramid views. ``api_path`` renders
    the ExtDirect API, ``router_path`` is the routing endpoint
    for ExtDirect calls.

    If the ``namespace`` argument is passed it will be used in
    the API as Ext namespace (default is 'Ext.app').

    If the ``descriptor`` argument is passed it's used as ExtDirect
    API descriptor name (default is Ext.app.REMOTING_API).

    If ``expose_exceptions`` argument is set to True the exception
    traceback will be exposed in the response object. WARNING this
    is potentially dangerous, do not use in production environments.

    The ``debug_mode`` argument will create a 'message' key in the
    response object pointing to a structure that can be used in pyramid
    debug toolbar.

    See http://www.sencha.com/products/js/direct.php for further infos.

    The optional ``expose_exceptions`` argument controls the output of
    an ExtDirect call - if ``True``, the router will provide additional
    information about exceptions.
    """

    def __init__(self, api_path="extdirect-api.js",
                 router_path="extdirect-router",
                 namespace='Ext.app',
                 descriptor='Ext.app.REMOTING_API',
                 expose_exceptions=True,
                 debug_mode=False,
                 json_encoder=JsonReprEncoder):
        self.api_path = api_path
        self.router_path = router_path
        self.namespace = namespace
        self.descriptor = descriptor
        self.expose_exceptions = expose_exceptions
        self.debug_mode = debug_mode
        self.actions = defaultdict(dict)
        self.json_encoder = json_encoder

    def add_action(self, action_name, **settings):
        """
        Registers an action.

        ``action_name``: Action name

        Possible values of `settings``:

        ``method_name``: Method name
        ``callback``: The callback to execute upon client request
        ``numargs``: Number of arguments passed to the wrapped callable
        ``accept_files``: If true, this action will be declared as formHandler in API
        ``permission``: The permission needed to execute the wrapped callable
        ``metadata``: Metadata definition
        ``request_as_last_param``: If true, the wrapped callable will receive a request object
            as last argument

        """
        callback_key = _mk_cb_key(action_name, settings['method_name'])
        self.actions[action_name][callback_key] = settings

    def get_actions(self):
        """ Builds and returns a dict of actions to be used in ExtDirect API """
        ret = {}
        for (key, val) in self.actions.items():
            items = []
            for settings in val.values():
                method_info = dict(
                    len=settings['numargs'],
                    name=settings['method_name']
                )
                if settings['accepts_files']:
                    method_info['formHandler'] = True
                meta = settings['metadata']
                if meta:
                    if isinstance(meta, ExtListMetadata):
                        method_info['metadata'] = {
                            'len': meta.numargs,
                            'strict': meta.strict
                        }
                    elif isinstance(meta, ExtDictMetadata):
                        method_info['metadata'] = {
                            'params': meta.param_names,
                            'strict': meta.strict
                        }
                items.append(method_info)
            ret[key] = items
        return ret

    def get_method(self, action, method):
        """ Returns a method's settings """
        if action not in self.actions:
            raise KeyError("Invalid action: {}".format(action))
        key = _mk_cb_key(action, method)
        if key not in self.actions[action]:
            raise KeyError("No such method in '{}': '{}'".format(action, method))
        return self.actions[action][key]

    def _get_api_dict(self, request):
        all_actions = self.get_actions()
        actions = dict()
        # filter returned actions in case there's an 'actions' request param
        if 'actions' in request.params:
            action_names = set([an for an in request.params['actions'].split(',') if an.strip()])
            for action in all_actions:
                if action in action_names:
                    actions[action] = all_actions[action]
        else:
            actions = all_actions
        # FIXME: use route_url instead of request.application_url + '/' + self.router_path,
        return dict(
            url=request.application_url + '/' + self.router_path,
            type='remoting',
            namespace=self.namespace,
            actions=actions
        )

    def dump_api(self, request):
        """ Dumps all known remote methods """
        return JS_API_TPL.format(
            namespace=self.namespace,
            descriptor=self.descriptor,
            api=json.dumps(self._get_api_dict(request))
        )

    def _do_route(self, action_name, method_name, params, metadata, trans_id, request):
        """ Performs routing, i.e. calls decorated methods/functions """
        if params is None:
            params = list()
        settings = self.get_method(action_name, method_name)
        permission = settings.get('permission', None)
        ret = {
            "type": "rpc",
            "tid": trans_id,
            "action": action_name,
            "method": method_name,
            "result": None
        }

        callback = settings['callback']

        append_request = settings.get('request_as_last_param', False)
        permission_ok = True
        context = request.root

        prepend = []
        if settings['class']:
            instance = settings['class'](request)
            prepend.append(instance)
            context = instance
        elif append_request:
            params.append(request)

        if settings['metadata']:
            prepend.append(metadata)

        params = prepend + params

        if permission is not None:
            permission_ok = has_permission(permission, context, request)

        try:
            if not permission_ok:
                raise AccessDeniedException("Access denied")
            ret["result"] = callback(*params)
        except Exception as exc:
            ret["type"] = "exception"
            # Let a user defined view for specific exception prevent returning
            # a server error.
            exception_view = render_view_to_response(exc, request)
            if exception_view is not None:
                ret["result"] = exception_view
                return ret

            # Log Error
            LOG.error("%s: %s", str(exc.__class__.__name__), exc)
            LOG.info(traceback.format_exc())

            if self.expose_exceptions:
                ret["result"] = {
                    'error': True,
                    'message': str(exc),
                    'exception_class': str(exc.__class__),
                    'stacktrace': traceback.format_exc()
                }
            else:
                message = 'Error executing {}.{}'.format(action_name, method_name)
                ret["result"] = {
                    'error': True,
                    'message': message
                }

            if self.debug_mode:
                # if pyramid_debugtoolbar is enabled, generate an interactive page
                # and include the url to access it in the ext direct Exception response text
                from pyramid_debugtoolbar.tbtools import get_traceback
                from pyramid_debugtoolbar.utils import EXC_ROUTE_NAME
                import sys
                exc_history = request.exc_history
                if exc_history is not None:
                    tb = get_traceback(
                        info=sys.exc_info(),
                        skip=1,
                        show_hidden_frames=False,
                        ignore_system_exceptions=True)
                    for frame in tb.frames:
                        exc_history.frames[frame.id] = frame
                    exc_history.tracebacks[tb.id] = tb

                    qs = {'token': exc_history.token, 'tb': str(tb.id)}
                    exc_url = request.route_url(EXC_ROUTE_NAME, _query=qs)
                    ret['message'] = 'Exception: traceback url: {}'.format(exc_url)
        return ret

    def route(self, request):
        """ Route a request to the corresponding action method """
        is_form_data = is_form_submit(request)
        if is_form_data:
            data = parse_extdirect_form_submit(request)
        else:
            data = parse_extdirect_request(request)
        ret = []
        for (act, meth, params, metadata, tid) in data:
            ret.append(self._do_route(act, meth, params, metadata, tid, request))
        if not is_form_data:
            if len(ret) == 1:
                ret = ret[0]
            return (json.dumps(ret, cls=self.json_encoder), False)
        ret = ret[0] # form data cannot be batched
        form_data = json.dumps(ret, cls=self.json_encoder).replace("&quot;", r"\&quot;")
        return (FORM_SUBMIT_RESPONSE_TPL.format(form_data), True)


class ExtMetadata(object):
    """ Base metadata class """

    def __init__(self, strict=True):
        self.strict = strict


class ExtListMetadata(ExtMetadata):
    """ Represents a metadata definition that will
        pass in an ordered list of parameters
        ``metadata`` arguments
    """

    def __init__(self, numargs=None, strict=True):
        super(ExtListMetadata, self).__init__(strict)
        if type(numargs) is not int or numargs < 1:
            raise ValueError("'numargs' has to be an int > 0")
        self.numargs = numargs


class ExtDictMetadata(ExtMetadata):
    """ Represents a metadata definition that will
        pass in a dict as ``metadata`` argument
        with members defined in ``param_names``
    """

    def __init__(self, param_names=None, strict=True):
        super(ExtDictMetadata, self).__init__(strict)
        if self.strict and not param_names:
            raise ValueError("Strict is set, please provide at least one param name")
        self.param_names = param_names


class extdirect_method(object): # pylint: disable=invalid-name, too-few-public-methods
    """Enables direct extjs access to python methods through json/form submit"""
    def __init__(self,
            action=None,
            method_name=None,
            permission=None,
            accepts_files=False,
            metadata=None,
            request_as_last_param=False):
        if metadata and not isinstance(metadata, ExtMetadata):
            raise ValueError("Metadata must be an instance of either ExtListMetadata or ExtDictMetadata")
        self.info = None
        self._settings = dict(
            action=action,
            method_name=method_name,
            permission=permission,
            accepts_files=accepts_files,
            metadata=metadata,
            request_as_last_param=request_as_last_param,
            original_name=None
        )

    def __call__(self, wrapped):
        original_name = wrapped.__name__
        self._settings["original_name"] = original_name
        if self._settings["method_name"] is None:
            self._settings["method_name"] = original_name

        self.info = venusian.attach(
            wrapped,
            self.register,
            category='extdirect'
        )
        return wrapped

    def _get_settings(self):
        return self._settings.copy()

    def register(self, scanner, name, obj):
        """ Venusian callback that registers a function
            or a class method as extdirect method
        """
        settings = self._get_settings()
        metadata = settings['metadata']

        class_context = isinstance(obj, type)

        settings['class'] = None
        if class_context:
            settings['class'] = obj
            callback = getattr(obj, settings["original_name"])
            numargs = callback.__code__.co_argcount
            # instance var doesn't count
            numargs -= 1
        else:
            if settings['action'] is None:
                raise ValueError("Decorated function has no action (name)")
            callback = obj
            numargs = callback.__code__.co_argcount

        if numargs and settings['request_as_last_param']:
            numargs -= 1

        if metadata:
            numargs -= 1
            if numargs < 0:
                raise ValueError("{} must provide at least one argument for metadata".format(settings['original_name']))

        settings['numargs'] = numargs

        action = settings.pop("action", None)
        if action is not None:
            name = action

        if class_context:
            class_settings = getattr(obj, '__extdirect_settings__', None)
            if class_settings:
                if action is None:
                    name = class_settings.get("default_action_name", name)
                if settings.get("permission") is None:
                    permission = class_settings.get("default_permission")
                    settings["permission"] = permission

        extdirect = scanner.config.registry.getUtility(IExtdirect)
        extdirect.add_action(name, callback=callback, **settings)


def is_form_submit(request):
    """ Checks if a request contains extdirect form submit """
    left_over = FORM_DATA_KEYS - set(request.params)
    return not left_over


def parse_extdirect_form_submit(request):
    """
        Extracts extdirect remoting parameters from request
        which are provided by a form submission
    """
    params = request.params
    action = params.get('extAction')
    method = params.get('extMethod')
    tid = params.get('extTID')
    metadata = params.get('extMetadata')
    if metadata:
        metadata = json.loads(metadata)
    data = dict()
    for key in params:
        if key not in FORM_DATA_KEYS:
            data[key] = params[key]
    return [(action, method, [data], metadata, tid)]


def parse_extdirect_request(request):
    """
        Extracts extdirect remoting parameters from request
        which are provided by an AJAX request
    """
    body = request.body
    decoded_body = json.loads(body.decode())
    ret = []
    if not isinstance(decoded_body, list):
        decoded_body = [decoded_body]
    for part in decoded_body:
        action = part['action']
        method = part['method']
        data = part['data']
        metadata = part.get('metadata', None)
        tid = part['tid']
        ret.append((action, method, data, metadata, tid))
    return ret


def api_view(request):
    """ Renders the API """
    extdirect = request.registry.getUtility(IExtdirect)
    body = extdirect.dump_api(request)
    return Response(body, content_type='text/javascript', charset='UTF-8')


def router_view(request):
    """ Renders the result of a ExtDirect call """
    extdirect = request.registry.getUtility(IExtdirect)
    (body, is_form_data) = extdirect.route(request)
    ctype = 'text/html' if is_form_data else 'application/json'
    return Response(body, content_type=ctype, charset='UTF-8')


def includeme(config):
    """ Let extdirect be included by config.include(). """
    settings = config.registry.settings
    extdirect_config = dict()
    names = ("api_path", "router_path", "namespace", "descriptor",
             "expose_exceptions", "debug_mode", "json_encoder")
    for name in names:
        qname = "pyramid_extdirect.{}".format(name)
        value = settings.get(qname, None)
        if name == "expose_exceptions" or name == "debug_mode":
            value = (value == "true")
        if name == "json_encoder" and value:
            from pyramid.path import DottedNameResolver
            resolver = DottedNameResolver()
            value = resolver.resolve(value)
        if value is not None:
            extdirect_config[name] = value

    extd = Extdirect(**extdirect_config)
    config.registry.registerUtility(extd, IExtdirect)

    api_view_perm = settings.get("pyramid_extdirect.api_view_permission")
    config.add_route('extapi', extd.api_path)
    config.add_view(api_view, route_name='extapi', permission=api_view_perm)

    router_view_perm = settings.get("pyramid_extdirect.router_view_permission")
    config.add_route('extrouter', extd.router_path)
    config.add_view(router_view, route_name='extrouter', permission=router_view_perm)

