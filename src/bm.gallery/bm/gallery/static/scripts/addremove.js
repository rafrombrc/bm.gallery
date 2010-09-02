function addField(selector, type) {
    var newElement = $(selector).clone(true);
    if (! $(newElement).find( 'a').length) {
        var a_remove = $('<a>remove</a>').attr({id : "remove"});
        $(newElement).append(a_remove);
        $(a_remove).click(function() {
            removeField(this, type);
        });
    };
    var total = $('#id_' + type + '-TOTAL_FORMS').val();
    newElement.find(':input').each(function() {
        var name = $(this).attr('name').replace('-' + (total-1) + '-','-' + total + '-');
        $(this).attr('name', name);
        var id = 'id_' + name;
        $(this).attr('id', id);
        $(this).attr('value', '');
    });
    newElement.find('label').each(function() {
        var newFor = $(this).attr('for').replace('-' + (total-1) + '-','-' + total + '-');
        $(this).attr('for', newFor);
    });
    total++;
    $('#id_' + type + '-TOTAL_FORMS').val(total);
    $(selector).after(newElement);
    $(newElement).hide();
    $(newElement).show(200);

    // max 10 uploads
    if (total >= 10) {
        $('#another').hide(400);
    };
};


function removeField(remove_link, type) {
    var parent_p = $(remove_link).closest("p");
    var total = $('#id_' + type + '-TOTAL_FORMS').val();

    var this_index = $("input", parent_p).attr("name").split("-")[1];
    var index = parseInt(this_index);
    $(parent_p).nextAll("p").each(function() {
        var name = $("input", this).attr("name").replace('-' + (index+1) + '-', '-' + index + '-');
        var id = 'id_' + name;
        $("input", this).attr("name", name);
        $("input", this).attr("id", id);
        $("label", this).attr("for", id);
        index++;
    });

    $(parent_p).hide(200, function() {
        $(parent_p).remove();
    });
    total--;
    $('#id_' + type + '-TOTAL_FORMS').val(total);

    // re-show the add another link if necessary
    if (total < 10) {
        $('#another').show(400);
    };
};