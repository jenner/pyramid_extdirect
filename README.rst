repoze.bfg.extdirect README
===========================

Introduction:
-------------

This `repoze.bfg`_ plugin provides a router for the `ExtDirect Sencha`_ API
included in `ExtJS 3.x`_ .

.. _`repoze.bfg`: http://bfg.repoze.org/
.. _`ExtDirect Sencha`: http://extjs.com/products/extjs/direct.php
.. _`ExtJS 3.x`: http://www.sencha.com/


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
code in BFG:

1) Create an application root and a set of ``controller`` instances that
   expose methods to be used in ExtDirect. This means we have to use
   the BFGs `traversal`_ features, so we're able to descend from our
   application root to an action (controller instance) and call its method.

2) Do not map ExtDirect actions to real instances in BFG, but instead *group*
   them using merely a name into actions and methods

.. _`traversal`: http://docs.repoze.org/bfg/1.3/glossary.html#term-traversal


Usage example:
--------------

We need to add the ``repoze.bfg.extdirect`` meta.zcml to our applications configure.zcml
so we're able to use the ``<extdirect ... />`` configuration directive::

    <configure xmlns="http://namespaces.repoze.org/bfg">

      <include package="repoze.bfg.includes" />
      <include package="repoze.bfg.extdirect" file="meta.zcml" />

      <extdirect
        api_name="extapi"
        api_path="extdirect-api.js"
        router_name="extrouter"
        router_path="extdirect-router"
        namespace="MyApp"
        descriptor="MyApp.REMOTE_API"
        permission="view"
        package="."
        />

        <!-- ... -->
    </configure>

You **have** to define ``api_name``/``api_path`` and ``router_name``/``router_path``
(both are used to create vanilla BFG views to the API renderer and ExtDirect router) and
the package parameter, which is used to scan the passed packaged/module for decorators (see below).

Define an application root and a set of controllers to be mapped as actions/methods (first approach),
the application root is the object returned by your BFG `root factory`_. Here's how it might look::

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

.. _`root factory`: http://docs.repoze.org/bfg/1.3/glossary.html#term-root-factory

The ``GridController`` class could combine all methods for grid operations::

    from repoze.bfg.extdirect import extdirect_method

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
encode/decode builtin python primitives. ``repoze.bfg.extdirect`` has a small helper
though, that checks if an object has a method called ``json_repr()`` (which should
return a JSON serializable dict/list/string/number/etc.) and if found, this method is
used to decode an instance to its JSONable version.
You can define a ``__extdirect_settings__`` property in a class to define a default
``action`` and ``permission``, so in the example above we could also just use ``@extdirect_method()``.

Using the second approach (without direct class/method mapping in python) we'd just
create a module (or even a package) with decorated functions instead of classes,
the code below would export exactly the same API to ExtDirect as the one from above::

    from repoze.bfg.extdirect import extdirect_method

    @extdirect_method(action='Grids')
    def loadGridData(params):
        # load grid and return s.th.


Sometimes you need to use the upload features of ExtDirect. Since uploads cannot
be done using AJAX (through JSON-encoded request body) Ext does a little trick
by creating a hidden iframe and posting a form within this iframe to the server.
However, ExtDirect needs to know in advance, that your code might receive uploads.
In ``repoze.bfg.extdirect`` decorators this is done by adding a ``accepts_files``
parameter to the ``@extdirect_method`` decorator::

    @extdirect_method(action='Users', accepts_files=True)
    def upload_user_picture(uploaded_file):
        # uploaded_file is now a FieldStorage instance


