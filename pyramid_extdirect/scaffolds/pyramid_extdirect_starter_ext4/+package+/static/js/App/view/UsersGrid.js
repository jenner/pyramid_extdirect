Ext.define('App.view.UsersGrid', {
    extend: 'Ext.grid.Panel',
    alias: 'widget.my-users-grid',
    requires: ['App.view.EditUserDialog'],
    store: 'Users',
    columns: [{
        header: 'ID',
        dataIndex: 'id',
        width: 80
    }, {
        header: 'Name',
        dataIndex: 'name',
        flex: 1
    }, {
        header: 'Title',
        dataIndex: 'title'
    }],

    dockedItems: [{
        dock: 'top',
        xtype: 'toolbar',
        items: [{
            xtype: 'button',
            tooltip: 'Add user...',
            glyph: 'xf055@FontAwesome',
            itemId: 'addButton'
        }, {
            xtype: 'button',
            tooltip: 'Edit user...',
            glyph: 'xf044@FontAwesome',
            itemId: 'editButton',
            disabled: true
        }, {
            xtype: 'button',
            tooltip: 'Delete user...',
            glyph: 'xf1f8@FontAwesome',
            itemId: 'deleteButton',
            disabled: true
        }]
    }, {
        dock: 'bottom',
        xtype: 'pagingtoolbar',
        store: 'Users',
        displayInfo: true
    }]

});
