Ext.define('App.model.User', {
    extend: 'Ext.data.Model',
    fields: [{
        name: 'id',
        type: 'int'
    }, {
        name: 'name',
        type: 'string'
    }, {
        name: 'title_id',
        type: 'int'
    }, {
        name: 'title',
        type: 'string'
    }, {
        name: 'description',
        type: 'string'
    }, {
        name: 'picture',
        type: 'string'
    }, {
        // synthetic prop used to distinguish between new and existing records
        name: 'isNew',
        type: 'boolean',
        defaultValue: false
    }]
});
