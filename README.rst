repoze.bfg.extdirect README
===========================

This `repoze.bfg`_ plugin provides a router for the `ExtDirect Sencha`_ API
included in `ExtJS 3.x`_ .

.. _`repoze.bfg`: http://bfg.repoze.org/
.. _`ExtDirect Sencha`: http://extjs.com/products/extjs/direct.php
.. _`ExtJS 3.0`: http://www.sencha.com/


ExtDirect allows to run server-side callbacks directly through JavaScript without
the extra AJAX boilerplate. The typical ExtDirect usage scenario goes like this:
    
    ...
    MyApp.SomeClass.fooMethod(foo, bar, function(provider, e) {
        if (e.status) {
            // do cool things with e.result
        } else {
            // display error message
        }
    });

or even better, if ExtDirect is used in a GridStore:

    var myStore = new Ext.grid.GridStore({
        directFn: MyApp.SomeOtherClass.loadGridData,
        // ...
    });

Here ``MyApp`` is the application namespace, ``SomeClass`` or
``SomeOtherClass`` are classes or ``actions`` and ``fooMethod`` and 
``loadGridData`` are methods.
