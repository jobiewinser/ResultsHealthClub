function freetastershandlehtmxbeforeRequest(evt){
    if (![undefined, ''].includes(evt.detail.pathInfo.path) && ![undefined, ''].includes(evt.detail.target.id)){
        if (evt.detail.target.id == 'overview_table' || evt.detail.pathInfo.path.includes("academy-booking-overview")){
            $("#overview_table").dataTable().fnDestroy();
        }
    }
}

function freetastershandlehtmxafterSwap(evt){
    if (evt.detail.xhr.status == 200){
        if (evt.detail.target.id == 'overview_table'){
            initDataTable(); 
        }           
    }
}