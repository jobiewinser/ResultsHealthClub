function leadshandlehtmxbeforeRequest(evt){
    if (![undefined, ''].includes(evt.detail.pathInfo.path) && ![undefined, ''].includes(evt.detail.target.id)){
        if (evt.detail.target.id == 'overview_table' || evt.detail.pathInfo.path.includes("academy-booking-overview")){
            $("#overview_table").dataTable().fnDestroy();
        }
    }
}

function leadshandlehtmxafterRequest(evt){
    if (evt.detail.xhr.status == 200){
        if (evt.detail.pathInfo.requestPath.includes("import-active-campaign-leads")){
            $('#generic_modal').modal('hide');
        }             
    }
}

function leadshandlehtmxafterSwap(evt){
    if (evt.detail.xhr.status == 200){
        if (![undefined, ''].includes(evt.detail.pathInfo.requestPath)){
            if (evt.detail.pathInfo.requestPath.includes("add-manual-booking")){
                $('#generic_modal').modal('hide');
                snackbarShow('Successfully added a booking', 'success')
            } else if (evt.detail.pathInfo.requestPath.includes("refresh-lead-article") || evt.detail.pathInfo.requestPath.includes("leads-and-calls") || evt.detail.pathInfo.requestPath.includes("refresh-leads-board")){
                document.getElementById('notification2').play();
                set_total_costs();
                set_lead_counts();                
            }
        }             
    }
}

function filterLeads(searchInput){
    if (
        searchInput.value != ""){
        jQuery.expr[':'].containsLower = function(elem, i, m) {
        let name_elem = $(elem).find('.lead_name');
        let campaign_elem = $(elem).find('.campaign_name');
        let site_elem = $(elem).find('.site_name');                        
        let cost_elem = $(elem).find('.lead_cost');
        let phone_elem = $(elem).find('.phone_number');
        let search_term = m[3].toLowerCase();
        return (
            (name_elem.html().toLowerCase()).includes(search_term) ||
            (campaign_elem.html().toLowerCase()).includes(search_term) ||
            (site_elem.html().toLowerCase()).includes(search_term) ||
            (cost_elem.html().toLowerCase()).includes(search_term) ||
            (phone_elem.html().toLowerCase()).includes(search_term)
        )
    };
    $('.column-drag').hide().filter(':containsLower("'+searchInput.value+'")').show();
} else {
    $('.column-drag').show();
}
}

function handleDraggedItem(dragged_elem, drag_target){
    // dragged_elem = $('#'+dragged_elem_id)
    console.log(dragged_elem, drag_target)
    var respStatus = $.ajax({
        type:'POST',
        url:'/new-call/'+dragged_elem.data('id')+'/'+$(drag_target).data("call-count")+'/'+$('#max_call_count').val()+'/',
        data:{'csrfmiddlewaretoken':csrftoken},
        success: function (data) {                
            // $('#refresh_column_metadata').click()
            snackbarShow('Successfully added call', 'success')
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
        }
    })
    let call_count = parseInt($(drag_target).data("call-count"));
    let max_call_count = parseInt($('#max_call_count').val());
    if (call_count > max_call_count) {
        $('#add_column').click();
    }
}

function set_total_costs(){  
    $('.total_cost').each(function () {
        let total_cost = 0.00;
        $(this).closest('.column-done').find(".lead_cost").each(function() {
        total_cost += parseFloat($(this).data('cost'));
        });
        total_cost = total_cost.toFixed(2);
        $(this).val(total_cost).html(total_cost);
    });
}

function set_lead_counts(){  
    $('.total_count').each(function () {
        let total_count = 0;
        $(this).closest('.column-done').find(".column-drag").each(function() {
            total_count += 1;
        });
        $(this).val(total_count).html(total_count);
    });
}

function lead_event_listener(identifier){
    $(identifier).mousedown(function() {
        drag_divs_showing = false;
    });
}
