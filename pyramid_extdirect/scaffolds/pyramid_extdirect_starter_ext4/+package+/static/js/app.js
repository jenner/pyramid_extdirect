Ext.direct.Manager.addProvider(Ext.app.REMOTING_API);
Ext.Loader.setConfig({enabled: true});

Ext.application({
    name: 'App',
    appFolder: 'static/js/App',
    controllers: ['Main'],
    launch: function() {
        Ext.require('App.view.Viewport', function() {
            Ext.widget('my-app-viewport');
        });
    }   
});
