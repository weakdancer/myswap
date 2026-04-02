window.thisPage = window.thisPage || {};
window.thisPage.isDirty = false;

window.thisPage.closeEditorWarning = function (event) {
    if (window.thisPage.isDirty)
        return 'It looks like you have been editing something' +
               ' - if you leave before saving, then your changes will be lost.'+
            '看上去你编辑了什么东西'+
            '-如果你离开前不保存，你编辑的内容将丢失。'
    else
        return undefined;
};

$("form").on('keyup', 'textarea', // You can use input[type=text] here as well.
             function () { 
                 window.thisPage.isDirty = true; 
             });

$("form").submit(function () {
    window.thisPage.isDirty = false;
});
window.onbeforeunload = window.thisPage.closeEditorWarning;

//credit: http://stackoverflow.com/questions/7317273/warn-user-before-leaving-page-with-unsaved-changes