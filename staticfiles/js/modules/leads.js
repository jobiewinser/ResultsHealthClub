function leadshandlehtmxbeforeRequest(evt){
    if (![undefined, ''].includes(evt.detail.pathInfo.path) && ![undefined, ''].includes(evt.detail.target.id)){
        if (evt.detail.target.id == 'overview_table' || evt.detail.pathInfo.path.includes("academy-booking-overview")){
            $("#overview_table").dataTable().fnDestroy();
        } else if (evt.detail.pathInfo.requestPath.includes("message-list")) {

        }
    }
}

function leadshandlehtmxafterSwap(evt){
    if (evt.detail.xhr.status == 200){
        if (![undefined, ''].includes(evt.detail.pathInfo.requestPath)){
            if (evt.detail.pathInfo.requestPath.includes("create-campaign-lead")){
                $('#generic_modal').modal('hide');
                // $('#refresh_column_metadata').click()
                snackbarShow('Successfully manually created a campaign lead', 'success')
            } else if (evt.detail.pathInfo.requestPath.includes("add-manual-booking")){
                $('#generic_modal').modal('hide');
                snackbarShow('Successfully added a booking', 'success')
            } else if (evt.detail.pathInfo.requestPath.includes("refresh-lead-article") || evt.detail.pathInfo.requestPath.includes("leads-and-calls")){
                document.getElementById('notification2').play();
                set_total_costs();
            }
        }             
    }
}

function handleDraggedItem(dragged_elem_id, drag_target){
    dragged_elem = $('#'+dragged_elem_id)
    var respStatus = $.ajax({
        type:'POST',
        url:'/campaign-leads/new-call/'+dragged_elem.data('id')+'/'+$(drag_target).data("call-count")+'/'+$('#max_call_count').val()+'/',
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