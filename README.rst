pyramid_extdirect README
===========================

Introduction:
-------------

This `pyramid`_ plugin provides a router for the `ExtDirect Sencha`_ API
included in `ExtJS`_ .

.. _`pyramid`: http://docs.pylonsproject.org/en/latest/docs/pyramid.html
.. _`ExtDirect Sencha`: https://docs.sencha.com/extjs/6.0/backend_connectors/direct/specification.html
.. _`ExtJS`: http://www.sencha.com/products/extjs/


ExtDirect allows to run server-side callbacks directly through JavaScript without
the extra AJAX boilerplate. The typical ExtDirect usage scenario goes like this::

    MyApp.SomeClass.fooMethod(foo, bar, function(response) {
        // do cool things with response
    });

or even better, if ExtDirect is used in a GridStore::

    var usersStore = new Ext.data.Store({
        fields: ['id', 'name', 'title'],
        proxy: {
            type: 'direct',
            directFn: MyApp.Users.loadAll,
            reader: {
                type: 'json',
                rootProperty: 'items'
            }
        }
        // ...
    });

Here ``MyApp`` is the application namespace, ``SomeClass`` or
``Grids`` are classes or *actions* and ``fooMethod`` and 
``loadGridData`` are methods.

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

Or, if you'd like to group your methods into classes (actions), you can do so by decoration
class methods:

The ``UsersController`` class could combine all methods for users CRUD operations, the only
requirement is that this class accepts ``request`` as its first and only constructor argument,
this is needed to make sure your methods have access to ``request`` at any time::

    from pyramid_extdirect import extdirect_method

    class UsersController(object):

        __extdirect_settings__ = { 
            'default_action_name': 'Users',
            'default_permission': 'view'
        }

        def __init__(self, request):
            self.request = request

        # we don't need to set ``action`` here, because
        # it's already defined via __extdirect_settings__
        @extdirect_method(permission='view', method_name='loadAll')
        def load_all(self, params):
            # params is a simple dict that will contain the
            # paging and sorting options as well as any other
            # extra parameters (defined using proxy.extraParams
            # your store config)
            users = []
            for user in users_db.fetch_all():
                users.append({
                    id: obj.id,
                    name: obj.name,
                    title: obj.title,
                    # ...
                })
            return dict(success=True, items=users)

As you can see, the ``Users#loadAll`` method doesn't even know it's been called through
a HTTP request, it's just a plain old python method which returns a dict.
The ``@extdirect_method(permission='view')`` decoration adds it to
the ``Users`` action (also making sure only users with *view* permission are allowed
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

    class Users(object):
        ...
        @extdirect_method(accepts_files=True)
        def upload_avatar(self, uploaded_file):
            # uploaded_file is now a FieldStorage instance

In some situations it is absolutely necessary to access the ``request`` object
in your functions and you don't want to create an extra class (where the request would be
passed in to the class constructor) -- this can be achieved by passing ``request_as_last_param`` to the
decorator::

    from pyramid.security import authenticated_userid

    @extdirect_method(action='App', request_as_last_param=True):
    def get_current_user(request):
        return authenticated_userid(request)

-- 
Igor Stroh, <igor.stroh -at- rulim.de>
