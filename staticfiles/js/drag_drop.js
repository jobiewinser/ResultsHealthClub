
var dragStart = target => {
    target.classList.add('dragging');
};

var dragEnd = target => {
    target.classList.remove('dragging');
    
    document.querySelector('#add_booking_area').classList.remove('shown');
    document.querySelector('#archive_area').classList.remove('shown');
    document.querySelector('#chat_bottom').classList.remove('temp_hidden');
};

var dragEnter = event => {
    console.log("test")
    event.currentTarget.classList.add('drop');
    // console.log("dragEnter")
};

var dragLeave = event => {
    event.currentTarget.classList.remove('drop');
    // console.log("dragLeave")
};
var drag_divs_showing = false;
var drag = event => {
    event.currentTarget.classList.add("dragging")
    event.dataTransfer.setData('text/html', event.currentTarget.outerHTML);
    event.dataTransfer.setData('text/plain', event.currentTarget.dataset.id);
    event.effectAllowed = "move";
    event.dataTransfer.dragEffect = "move";
    event.dataTransfer.dropEffect = "move";
    drag_divs_showing = true;
    setTimeout(function(){
        if (drag_divs_showing) {
            document.querySelector('#add_booking_area').classList.add('shown');
            document.querySelector('#archive_area').classList.add('shown');
            document.querySelector('#chat_bottom').classList.add('temp_hidden');
        }
    }, 200); 
};

var drop = event => {
    document.querySelectorAll('.column').forEach(column => column.classList.remove('drop'));
    let dragged_elem = document.querySelector(`[data-id="${event.dataTransfer.getData('text/plain')}"]`)
    let dragged_elem_id = dragged_elem.id
    dragged_elem.remove();
    
    event.preventDefault();
    event.currentTarget.innerHTML = event.dataTransfer.getData('text/html') + event.currentTarget.innerHTML;
    handleDraggedItem(dragged_elem_id, event.currentTarget)
    // console.log("drop", event.currentTarget)
    drag_divs_showing = false;
    document.querySelector('#add_booking_area').classList.remove('shown');
    document.querySelector('#archive_area').classList.remove('shown');
    document.querySelector('#chat_bottom').classList.remove('temp_hidden');
};

var drop_booking = event => {
    let dragged_elem = $(`[data-id="${event.dataTransfer.getData('text/plain')}"]`)
    event.preventDefault();
    // console.log("drop_booking", event.currentTarget)
    drag_divs_showing = false;
    document.querySelector('#add_booking_area').classList.remove('shown');
    document.querySelector('#archive_area').classList.remove('shown');
    document.querySelector('#chat_bottom').classList.remove('temp_hidden');
    
    htmx.ajax('GET', '/campaign-leads/campaign-lead-get-modal-content/'+dragged_elem.data('id')+'/?template_name=add_booking', {target:'#generic_modal_body'})
};

var drop_archive = event => {
    let dragged_elem = $(`[data-id="${event.dataTransfer.getData('text/plain')}"]`)
    event.preventDefault();
    // console.log("drop_booking", event.currentTarget)
    drag_divs_showing = false;
    document.querySelector('#add_booking_area').classList.remove('shown');
    document.querySelector('#archive_area').classList.remove('shown');
    document.querySelector('#chat_bottom').classList.remove('temp_hidden');
    console.log("#lead_pk_"+dragged_elem.data('id'))
    htmx.ajax('POST', '/campaign-leads/mark-done/'+dragged_elem.data('id')+'/', {swap:'none'})
};

// function handleDraggedItem(elem){
//     // console.log("handleDraggedItem")
// }

var allowDrop = event => {
    event.preventDefault();
};

// document.querySelectorAll('.column').forEach(column => {
//     column.addEventListener('dragenter', dragEnter);
//     column.addEventListener('dragleave', dragLeave);
// });

// document.addEventListener('dragstart', e => {
//     if (e.target.className.includes('column-drag')) {
//         dragStart(e.target);
//     }
// });

document.addEventListener('dragend', e => {
    if (e.target.className.includes('column-drag')) {
        dragEnd(e.target);
    }
});