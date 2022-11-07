
var dragStart = target => {
    target.classList.add('dragging');
    // console.log("dragStart")
};

var dragEnd = target => {
    target.classList.remove('dragging');
    document.querySelector('#add_booking_area').classList.remove('shown');
    document.querySelector('#chat_bottom').classList.remove('temp_hidden');
    // console.log("dragEnd", target)
};

var dragEnter = event => {
    event.currentTarget.classList.add('drop');
    // console.log("dragEnter")
};

var dragLeave = event => {
    event.currentTarget.classList.remove('drop');
    // console.log("dragLeave")
};

var drag = event => {
    event.dataTransfer.setData('text/html', event.currentTarget.outerHTML);
    event.dataTransfer.setData('text/plain', event.currentTarget.dataset.id);
    // console.log("drag")
    document.querySelector('#add_booking_area').classList.add('shown');
    document.querySelector('#chat_bottom').classList.add('temp_hidden');
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
    document.querySelector('#add_booking_area').classList.remove('shown');
    document.querySelector('#chat_bottom').classList.remove('temp_hidden');
};

var drop_booking = event => {
    let dragged_elem = $(`[data-id="${event.dataTransfer.getData('text/plain')}"]`)
    event.preventDefault();
    // console.log("drop_booking", event.currentTarget)
    document.querySelector('#add_booking_area').classList.remove('shown');
    document.querySelector('#chat_bottom').classList.remove('temp_hidden');
    
    htmx.ajax('GET', '/campaign-leads/campaign-lead-get-modal-content/'+dragged_elem.data('id')+'/?template_name=add_booking', {target:'#generic_modal_body'})
};

function handleDraggedItem(elem){
    // console.log("handleDraggedItem")
}

var allowDrop = event => {
    event.preventDefault();
};

document.querySelectorAll('.column').forEach(column => {
    column.addEventListener('dragenter', dragEnter);
    column.addEventListener('dragleave', dragLeave);
});

document.addEventListener('dragstart', e => {
    if (e.target.className.includes('column-drag')) {
        dragStart(e.target);
    }
});

document.addEventListener('dragend', e => {
    if (e.target.className.includes('column-drag')) {
        dragEnd(e.target);
    }
});