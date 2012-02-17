var batchedit = {
    init : function() {
        $('.button').button();
        $('div.delete input').click(function() {
            var elt = $(this), prefix, pos, work;
            if (elt.attr('checked') === "checked") {
                elt.parents('tr').find('.required').removeClass('required').addClass('wasrequired');
            }
            else {
                elt.parents('tr').find('.wasrequired').removeClass('wasrequired').addClass('required');
            }
        });

        // slap a "required" class on each form element inside a "required" div
        // which lets the validate plugin do its business
        var form = $('#batchedit');
        form.find('div.required').each(
            function() {
                $(this).find('input').addClass('required');
            }
        );

        // Add numeric validation to digits divs
        form.find('div.digits').each(
            function() {
                $(this).find('input').addClass('digits');
            }
        );

        $('.choicelist ul').makeacolumnlists({
            cols: 2,
            colWidth: 100
        });

        $('form.batchedit').validate({
            errorElement: 'p',
            errorPlacement: function(error, element) {
                error.appendTo(element.parents('div.required'));
            }
        });
    }
};

$(function() {
    batchedit.init();
});
