Ext.define('App.view.TitlesCombo', {
    extend: 'Ext.form.field.ComboBox',
    alias: 'widget.my-titles-combo',
    store: 'Titles',
    minChars: 1,
    displayField: 'title',
    valueField: 'id',
    forceSelection: true,
    triggerAction: 'all',
    queryMode: 'remote'
});
