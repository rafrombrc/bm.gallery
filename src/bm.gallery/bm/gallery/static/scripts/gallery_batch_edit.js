var batchedit = {
    init : function() {
        $('.button').button();
        $('div.delete input').click(function() {
            var elt = $(this), prefix, pos, work;
            if (elt.val() === "on") {
                prefix = elt.attr('id');
                pos = prefix.search('DELETE');
                prefix = prefix.substr(0, pos);
                work = $('#' + prefix + 'title');
                if (!work.val()) {
                    work.val('TO DELETE');
                }
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
            debug: true,
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
