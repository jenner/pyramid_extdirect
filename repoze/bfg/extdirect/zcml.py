from zope.interface import Interface
from zope.configuration.fields import GlobalObject
from zope.schema import TextLine

from repoze.bfg.zcml import route, utility
from repoze.bfg.path import caller_package, caller_module

from repoze.bfg.extdirect import api_view, router_view
from repoze.bfg.extdirect import Extdirect, IExtdirect

import os


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

def conf_handler(context,
        api_name,
        api_path,
        router_name,
        router_path,
        for_=None,
        permission=None,
        namespace=None,
        descriptor=None,
        package=None):
    # create and configure utility
    if package is None:
        package = "."
    app = context.resolve(package)
    extd = Extdirect(app, api_path, router_path, namespace=namespace, descriptor=descriptor)
    utility(context, component=extd, provides=IExtdirect)
    # add api view
    route(context, api_name, api_path, view=api_view, permission=permission, for_=for_)
    # add router view
    route(context, router_name, router_path, view=router_view, permission=permission, for_=for_)
