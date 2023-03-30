function chatCountdown(time, customer_number, whatsappnumber_pk, display_identifier, identifier) {
    let timer = setInterval(() => {
        console.log(time)
        time--;
        if (time <= 0) {
            clearInterval(timer);
            reloadChatWindow(customer_number, whatsappnumber_pk, identifier);
        }
        if (!$(identifier).length) {
            console.log(identifier ,$(identifier))
            clearInterval(timer);
        }
        $(display_identifier).html(formatSecondsToDateTime(time))
    }, 1000);
}
  
function reloadChatWindow(customer_number, whatsappnumber_pk, identifier){
    if ($(identifier).length) {
        htmx.ajax('GET', "/message-window/"+customer_number+"/"+whatsappnumber_pk+"/refresh/", {swap:"outerHTML", indicator:"#htmx_indicator_messageCollapse_"+whatsappnumber_pk, target:identifier})
    } else {
        // Element does not exist
    }
}
function formatSecondsToDateTime(seconds) {
    let date = new Date(null);
    date.setSeconds(seconds);
    return date.toISOString().substr(11, 8);
  }
  