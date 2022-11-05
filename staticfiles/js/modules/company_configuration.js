function companyconfigurationhandlehtmxafterRequest(evt){
    if (evt.detail.xhr.status == 500){
        $('.reset_on_error').each(function() {
            if (![undefined, ''].includes((this).data('value'))){
                $(this).data('value')
                $(this).val($(this).data('value'));
            }
        });
    };
}