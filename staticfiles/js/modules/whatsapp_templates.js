
// function initDataTable() {
//     try{$("#overview_table").dataTable().fnDestroy();}catch{}

//     dt = $('#overview_table').DataTable(          
//         {  
//             order: [[0, 'desc' ]],
//             iDisplayLength: 10,
//             search: {
//                 search: SearchTerm
//             }
//         }
//     );
//     let searchInput = $('#overview_table_filter').find('input');
//     searchInput.on('input', function (e) {
//         SearchTerm = searchInput.val()
//     });
// }
function whatsapptemplateshandlehtmxafterSwap(evt){
}

function whatsapptemplateshandlehtmxafterRequest(evt){
    if (evt.detail.xhr.status == 200){
        if (evt.detail.pathInfo.requestPath.includes('whatsapp-change-template-site')){
            $('#generic_modal').modal('hide');
            snackbarShow('Successfully transferred template', 'success')
        }else if (evt.detail.pathInfo.requestPath.includes('whatsapp-approval')){
            location.reload();
        }
    }
}