import os

from pyramid_zcml import route
from pyramid_zcml import utility
from zope.interface import Interface
from zope.configuration.fields import GlobalObject
from zope.schema import TextLine, Bool

from pyramid.extdirect import api_view, router_view
from pyramid.extdirect import Extdirect, IExtdirect



class IExtdirectDirective(Interface):

    api_name = TextLine(title=u'API Name', required=True)
    
    router_name = TextLine(title=u'Router Name', required=True)

    api_path = TextLine(
        title=u"API View javascript URI (path)",
        description=u"""The path under which the api is accessible in your application,
        The path shows up in URLs/paths. For example 'extdirect-api.js' or 'jsapp/api'.""",
        required=True,
        )

    router_path = TextLine(
        title=u"Router View javascript URI (path)",
        description=u"""The path under which the api is accessible in your application,
        The path shows up in URLs/paths. For example 'extdirect-api.js' or 'jsapp/api'.""",
        required=True,
        )

    for_ = GlobalObject(
        title=u"The interface or class this view is for.",
        required=False
        )

    namespace = TextLine(
        title=u"Namespace",
        description=u"A namespace for actions, defaults to 'Ext.app.REMOTING_API'",
        required=False
        )

    descriptor = TextLine(
        title=u"Descriptor",
        description=u"The API descriptor, used by ExtJS in addProvider() call",
        required=False
        )

    permission = TextLine(
        title=u"Permission",
        description=u"The permission needed to use the view.",
        required=False
        )

    package = TextLine(
        title=u"Package",
        description=u"Dotted path to python package containing decorated methods",
        required=False
        )

    expose_exceptions = Bool(
        title=u"Expose Exceptions",
        description=u"If true show a stacktrace of the original Exception in JSON output",
        required=False
        )

def conf_handler(context,
        api_name,
        api_path,
        router_name,
        router_path,
        for_=None,
        permission=None,
        namespace=None,
        descriptor=None,
        package=None,
        expose_exceptions=False):
    # create and configure utility
    if package is None:
        package = "."
    app = context.resolve(package)
    extd = Extdirect(app, api_path, router_path, namespace=namespace, descriptor=descriptor, expose_exceptions=expose_exceptions)
    utility(context, component=extd, provides=IExtdirect)
    # add api view
    route(context, api_name, api_path, view=api_view, permission=permission, for_=for_)
    # add router view
    route(context, router_name, router_path, view=router_view, permission=permission, for_=for_)
    extd.scan()
