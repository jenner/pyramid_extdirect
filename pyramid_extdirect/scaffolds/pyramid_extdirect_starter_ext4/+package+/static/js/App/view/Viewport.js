Ext.define('App.view.Viewport', {
    extend: 'Ext.container.Viewport',
    alias: 'widget.my-app-viewport',
    requires: ['App.view.UsersGrid'],
    layout: 'fit',
    items: {
        xtype: 'my-users-grid',
        title: 'Edit users',
        margin: 5
    }    
});
