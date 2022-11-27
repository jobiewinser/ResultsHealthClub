function initBookingDataTable() {
    console.log("initBookingDataTable")
    try{dt.fnDestroy();}catch{}
    
    var dt = $('#overview_table').DataTable(            
    {  
        order: [[ 4, 'asc' ],[ 2, 'asc' ]],
        iDisplayLength: 10
    }
    );
}

function bookinghandlehtmxafterSwap(evt){
    if (evt.detail.target.id == 'overview_table_span_wrapper'){
        initBookingDataTable(); 
    }
    if (evt.detail.xhr.status == 200){
        if (![undefined, ''].includes(evt.detail.pathInfo.path)){
            if (evt.detail.pathInfo.path.includes("mark-archived")){
                snackbarShow('Successfully marked lead as done', 'success')
            } else if (evt.detail.pathInfo.path.includes("add-manual-booking")){
                $('#generic_modal').modal('hide');
                snackbarShow('Successfully added a booking', 'success')
            } else if (evt.detail.pathInfo.path.includes("create-campaign-lead")){
                $('#refresh_overview_table').click(); 
                $('#generic_modal').modal('hide');
                snackbarShow('Successfully manually created a campaign lead', 'success')
            } else if (evt.detail.pathInfo.path.includes("mark-arrived")){
                $('#generic_modal').modal('hide');
                snackbarShow('Successfully marked that the customer arrived as booking', 'success')
            } else if (evt.detail.pathInfo.path.includes("mark-sold")){
                $('#generic_modal').modal('hide');
                snackbarShow('Successfully sold to customer', 'success')
            } else if (evt.detail.pathInfo.path.includes("campaign-booking-overview")){
                $('#refresh_campaign_list_span').click(); 
                snackbarShow('Successfully refreshed table', 'success')
            }                
        }                
    }
}
function bookinghandlehtmxbeforeRequest(evt){
    // if (![undefined, ''].includes(evt.detail.pathInfo.path) && ![undefined, ''].includes(evt.detail.target.id)){
        if (evt.detail.target.id == 'overview_table'){
            $("#overview_table").dataTable().fnDestroy();
        }
    // }
}

function whatsapptemplateshandlehtmxafterRequest(evt){
    if (evt.detail.xhr.status == 200){
        if (evt.detail.pathInfo.requestPath.includes('add-manual-booking')){
            $('#generic_modal').modal('hide');
            snackbarShow('Successfully added booking', 'success')
        }
    }
}