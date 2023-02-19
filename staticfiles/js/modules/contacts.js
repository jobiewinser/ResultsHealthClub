function contactshandlehtmxafterSwap(evt){
    if (evt.detail.xhr.status == 200){
        if (![undefined, ''].includes(evt.detail.pathInfo.requestPath)){
            if (evt.detail.pathInfo.requestPath.includes("edit-contact")){
                $('#generic_modal').modal('hide');
                snackbarShow('Successfully edited contact', 'success')
            } else if (evt.detail.pathInfo.requestPath.includes("add-contact")){
                snackbarShow('Successfully added contact', 'success')
            }
        }
    }
}