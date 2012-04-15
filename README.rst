pyramid_extdirect README
===========================

Introduction:
-------------

This `pyramid`_ plugin provides a router for the `ExtDirect Sencha`_ API
included in `ExtJS`_ .

.. _`pyramid`: http://docs.pylonsproject.org/docs/pyramid.html
.. _`ExtDirect Sencha`: http://extjs.com/products/extjs/direct.php
.. _`ExtJS`: http://www.sencha.com/products/extjs/


ExtDirect allows to run server-side callbacks directly through JavaScript without
the extra AJAX boilerplate. The typical ExtDirect usage scenario goes like this::

    MyApp.SomeClass.fooMethod(foo, bar, function(provider, e) {
        if (e.status) {
            // do cool things with e.result
        } else {
            // display error message
        }
    });

or even better, if ExtDirect is used in a GridStore::

    var myStore = new Ext.grid.GridStore({
        directFn: MyApp.Grids.loadGridData,
        baseParams: {
            obj_id: 1
        },
        paramsAsHash: true,
        // ...
    });

Here ``MyApp`` is the application namespace, ``SomeClass`` or
``Grids`` are classes or *actions* and ``fooMethod`` and 
``loadGridData`` are methods.

There are two approaches to map these actions and methods to python
code in Pyramid:

1) Create an application root and a set of ``controller`` instances that
   expose methods to be used in ExtDirect. This means we have to use
   Pyramid's `traversal`_ features, so we're able to descend from our
   application root to an action (controller instance) and call its method.

2) Do not map ExtDirect actions to real instances in Pyramid, but instead *group*
   them using merely a name into actions and methods

.. _`traversal`: http://docs.pylonsproject.org/projects/pyramid/dev/glossary.html#term-traversal


Usage example:
--------------

The minimum requirement for pyramid_extdirect is to create an ExtDirect API and Router::

    from pyramid.config import Configurator
    from exampleapp.resources import Root

    def main(global_config, **settings):
        """ This function returns a Pyramid WSGI application.
        """
        config = Configurator(root_factory=Root, settings=settings)
        config.add_view('exampleapp.views.my_view',
                        context='exampleapp:resources.Root',
                        renderer='exampleapp:templates/mytemplate.pt')
        config.add_static_view('static', 'exampleapp:static')
        # let pyramid_extdirect create all the needed views automatically
        config.include('pyramid_extdirect')
        # scan your code once to make sure the @extdirect_method decorators
        # are picked up
        config.scan()
        return config.make_wsgi_app()

After this you can decorate arbitrary functions or class methods using @extdirect_method::

    @extdirect_method(action='SomeAction')
    def do_stuff(a, b, c):
        return a + b + c

Or, if you'd like to group your methods into classes (actions), you can define an application
root and a set of controllers to be mapped as actions/methods, the application root is the
object returned by your Pyramid `root factory`_. Here's how it might look::

    class AppRoot(object):
        __name__ = None
        __parent__ = None

        def __init__(self):
            self.components = { 
                'grids': GridsController(),
            }

        def __getitem__(self, key):
            ret = self.components[key]
            ret.__name__ = key 
            ret.__parent__ = self
            return ret 

        def __iter__(self):
            return self.components.iterkeys()

.. _`root factory`: http://docs.pylonsproject.org/projects/pyramid/dev/glossary.html#term-root-factory

The ``GridController`` class could combine all methods for grid operations::

    from pyramid_extdirect import extdirect_method

    class GridController(object):
        __name__ = 'grids'

        __extdirect_settings__ = { 
            'default_action_name': 'Grids',
            'default_permission': 'view'
        }

        @extdirect_method(action='Grids', permission='view')
        def loadGridData(self, params):
            // params is a simple dict
            ret = []
            for obj in GridModel.fetch_stuff_by_id(params['obj_id']):
                ret.append({
                    id: obj.id,
                    title: obj.title,
                    # ...
                })
            return ret

As you can see, the ``loadGridData`` method doesn't even know it's bee called through
a HTTP request, it's just a plain old python method which returns a list of dicts.
The ``@extdirect_method(action='Grids', permission='view')`` decoration adds it to
the ``Grids`` action (also making sure only users with *view* permission are allowed
to run it). We're returning a ``dict`` here simply because the AJAX response sent to
the client has to be JSON serializable. By default python JSON marshallers can only
encode/decode builtin python primitives. ``pyramid_extdirect`` has a small helper
though, that checks if an object has a method called ``json_repr()`` (which should
return a JSON serializable dict/list/string/number/etc.) and if found, this method is
used to decode an instance to its JSONable version.
You can define a ``__extdirect_settings__`` property in a class to define a default
``action`` and ``permission``, so in the example above we could also just use ``@extdirect_method()``.

Sometimes you need to use the upload features of ExtDirect. Since uploads cannot
be done using AJAX (through JSON-encoded request body) Ext does a little trick
by creating a hidden iframe and posting a form within this iframe to the server.
However, ExtDirect needs to know in advance, that your code might receive uploads.
In ``pyramid_extdirect`` decorators this is done by adding a ``accepts_files``
parameter to the ``@extdirect_method`` decorator::

    @extdirect_method(action='Users', accepts_files=True)
    def upload_user_picture(uploaded_file):
        # uploaded_file is now a FieldStorage instance

Also, in some situations it is absolutely necessary to access the ``request`` object
in your functions, this can be achieved by passing ``request_as_last_param`` to the
decorator::

    from pyramid.security import authenticated_userid

    @extdirect_method(action='App', request_as_last_param=True):
    def get_current_user(request):
        return authenticated_userid(request)


That's all folks, enjoy!
-- 
Igor Stroh, <igor.stroh -at- rulim.de>
