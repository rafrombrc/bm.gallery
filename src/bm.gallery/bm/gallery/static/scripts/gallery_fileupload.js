/*jshint browser:true,undef:true,eqeqeq:false,nomen:true,white:false,plusplus:false,onevar:true */
/*global, log, window, $ */

var gallery = {
    fileelement : null,
    hasContinue : false,

    batchname_update : function() {
        var form = gallery.fileelement.find('form'), url, data, element;

        element = form.find('#update_batchname a');

        data = form.serialize();
        url = '/upload/batchname';
        $.post(url, data, gallery.batchname_update_response, 'json');
        return false;
    },

    batchname_update_response : function(data) {
        $('#update_batchname').append('&nbsp;<i>Updated!</i>');
    },

    init_fileupload : function(element, video) {
        gallery.fileelement = $(element);
        var types;

        if (video) {
            types = /(\.|\/)(zip|tar|tgz|tbz|tar\.gz|tar\.bz|gif|jpe?g|png|avi|mpe?g|m1v|mp2|mpa|mpe|mpv2|asf|mov|qt)$/i;
        }
        else {
            types = /(\.|\/)(zip|tar|tgz|tbz|tar\.gz|tar\.bz|gif|jpe?g|png)$/i;
        }
        gallery.fileelement.fileupload({
            dropZone: $(element),
            acceptFileTypes: types
        }).bind('fileuploaddone',function(e, data) {
            if (data.textStatus === 'success') {
                gallery.lastdata = data;
                $('#id_batchname').val(data.batchname);
                gallery.show_continue(data.result[0]);
            }
            return true;
        });

        // Load existing files:
        $.getJSON($(element + ' form').prop('action'), function (files) {
            var fu = $('#fileupload').data('fileupload');
            fu._adjustMaxNumberOfFiles(-files.length);
            fu._renderDownload(files)
                .appendTo($(element + ' .files'))
                .fadeIn(function () {
                    // Fix for IE7 and lower:
                    $(this).show();
                });
        });

        // Open download dialogs via iframes,
        // to prevent aborting current uploads:
        $(element + ' .files a:not([target^=_blank])').live('click', function (e) {
            e.preventDefault();
            $('<iframe style="display:none;"></iframe>')
                .prop('src', this.href)
                .appendTo('body');
        });
    },

    show_continue : function(data) {
        if (!gallery.hasContinue) {
            var btns = '<p class="continuebutton"><a href="/batch/' + data.batchid + '/edit/">Add Information</a> or <a href="/batch/' + data.batchid + '/later/">Come back later</a>';
            gallery.fileelement.before(btns).after(btns);

            $('#update_batchname').remove();
            $('#id_batchname').after('&nbsp;<span id="update_batchname"><a class="button" href="#">Update</a></span>');
            $('.continuebutton a').button();
            $('#update_batchname a').bind('click', gallery.batchname_update);
            gallery.hasContinue = true;
        }
        else {
            $('#id_batchname').val(data.batchname);
        }
    }

};