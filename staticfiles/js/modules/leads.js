// function initDataTable() {
//     try{dt.fnDestroy();}catch{}
    
//     dt = $('#overview_table').DataTable(            
//     {  
//         order: [[ 4, 'asc' ],[ 2, 'asc' ]],
//         iDisplayLength: 10
//     }
//     );
// }

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