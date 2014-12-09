Ext.define('App.view.EditUserDialog', {
    extend: 'Ext.window.Window',
    alias: 'widget.edit-user-dialog',
    requires: ['App.view.TitlesCombo'],
    constrain: true,
    modal: true,
    layout: 'fit',
    width: 300,
    minWidth: 300,
    height: 400,
    minHeight: 400,
    defaultFocus: 'nameField',
    config: {
        userRecord: null
    },
    items: [{
        xtype: 'form',
        bodyPadding: 5,
        defaults: {
            labelAlign: 'top',
            msgTarget: 'side',
            anchor: '100%'
        },
        items: [{
            xtype: 'textfield',
            fieldLabel: 'Name',
            allowBlank: false,
            itemId: 'nameField',
            name: 'name'
        }, {
            xtype: 'my-titles-combo',
            fieldLabel: 'Title',
            name: 'title_id'
        }, {
            xtype: 'textarea',
            fieldLabel: 'Description',
            name: 'description',
            anchor: '100% -105'
        }],
        buttonAlign: 'center',
        buttons: [{
            text: 'OK',
            itemId: 'okButton',
            formBind: true,
            disabled: true
        }, {
            text: 'Cancel',
            itemId: 'cancelButton'
        }]
    }],


});
