function campaignconfigurationhandlehtmxbeforeRequest(evt){
    if (![undefined, ''].includes(evt.detail.pathInfo.path) && ![undefined, ''].includes(evt.detail.target.id)){
        if (evt.detail.target.id == 'overview_table'){
            $("#overview_table").dataTable().fnDestroy();
        }
    }
}

function initCampaignConfigurationDataTable() {
    console.log("initCampaignConfigurationDataTable")
    
    $("#overview_table").dataTable().fnDestroy();
    
    var dt = $('#overview_table').DataTable();
}