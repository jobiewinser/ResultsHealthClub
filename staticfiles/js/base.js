var OriginalTitle = document.title;
var PageTitleNotification = {
    Vars:{
        
        Interval: null
    },    
    On: function(notification, intervalSpeed){
        this.Vars
        var _this = this;
        _this.Vars.Interval = setInterval(function(){
             document.title = (OriginalTitle == document.title)
                                 ? notification
                                 : OriginalTitle;
        }, (intervalSpeed) ? intervalSpeed : 1000);
    },
    Off: function(){
        clearInterval(this.Vars.Interval);
        document.title = OriginalTitle;   
    }
}

function basehandlehtmxafterSwap(evt){
    if (evt.detail.target.id == 'generic_modal_body'){
        $('#generic_modal').modal('show');
    }
    
    if (![undefined, ''].includes(evt.detail.pathInfo.requestPath)){
        if (evt.detail.pathInfo.requestPath.includes("message-window")){
            let element = $(evt.target.lastElementChild).find(".chat_card_body");
            try{
                element.scrollTop(element[0].scrollHeight - element[0].clientHeight);
            }catch(e){}
        } 
    
    }
    if (![undefined, ''].includes(evt.detail.pathInfo.path)){
        if (evt.detail.pathInfo.path.includes("modify-user")){
            $('#generic_modal').modal('hide');
            snackbarShow('Successfully modifed/added user', 'success')
        }
    }
    if (evt.detail.xhr.status == 200){
    } else {
        snackbarShow(evt.detail.xhr.responseText, 'danger')
    }
    $('.popover').remove()
    $('[data-bs-toggle=popover]').popover();
    $('[data-bs-toggle=popover_delay]').popover({
        delay: { 
           show: "350", 
           hide: "100"
        }
    });
}

function basehandlehtmxafterRequest(evt){   
    $('.popover').remove()
    let status = evt.detail.xhr.status;
    let srcElement = $(evt.srcElement);
    if(status == 200) {
        if (![undefined, ''].includes(evt.detail.pathInfo.path)){
            if (evt.detail.pathInfo.path.includes("login")){
                window.location.replace("/");
            }
        }
        if (![undefined, ''].includes(evt.detail.pathInfo.requestPath)){
            if (evt.detail.pathInfo.requestPath.includes("login-htmx")){
                snackbarShow('Successfully logged in', 'success');
                location.reload();
            }else if (evt.detail.pathInfo.requestPath.includes("modify-user")){
                snackbarShow('Successfully logged in', 'success');
                location.reload();
            }else if (evt.detail.pathInfo.requestPath.includes("update-message-counts")){
                document.getElementById('notification1').play();
                // PageTitleNotification.On("Message Sent/Received!", 1000);         
                // setTimeout(function() {
                //     PageTitleNotification.Off();
                // }, 2000);
            }else if (evt.detail.pathInfo.requestPath.includes("send-new-template-message")){
                $('#generic_modal').modal('hide');
                snackbarShow('Successfully sent message', 'success')
            }else if (evt.detail.pathInfo.requestPath.includes("add-whatsapp-business-account")){
                $('#generic_modal').modal('hide');
                snackbarShow('Successfully added phone', 'success')
            }else if (evt.detail.pathInfo.requestPath.includes("create-lead-note")){
                $('#generic_modal').modal('hide');
                snackbarShow('Successfully added note', 'success')
            }
            
            
        }
    } else if (status == 404) {   
        if (evt.detail.pathInfo.requestPath.includes("login-htmx")){ 
            $('#login_error').remove();                  
            srcElement.after("<div id='login_error' style='color:red'>Not Found</div>");
        }
        snackbarShow('Error: '+evt.detail.xhr.response, 'danger', display_ms=5000)           
    }else if (status == 500){
        snackbarShow('Error: '+evt.detail.xhr.response, 'danger', display_ms=5000)           
    }else if (status == 400){
        snackbarShow('Error: '+evt.detail.xhr.response, 'danger', display_ms=5000)           
    }
}

function basehandlehtmxoobAfterSwap(evt){
    if ($(evt.detail.target).hasClass('chat_card_body')){                        
        $(evt.detail.target).animate({
            scrollTop: $(evt.detail.target)[0].scrollHeight - $(evt.detail.target)[0].clientHeight
        }, 100);
    }
    $("[data-bs-toggle=popover]").popover();
}

function basehandlehtmxoobBeforeSwap(evt){    
    if ($(evt.target).hasClass('message_list_body')){
        htmx.ajax('GET', "/update-message-counts/", {swap:'none'})
    }
    $("[data-bs-toggle=popover]").popover();
}



function isCalendlyEvent(e) {
    return e.origin === "https://calendly.com" && e.data.event && e.data.event.indexOf("calendly.") === 0;
};

function inlinePreventDefault(e) {
    e.preventDefault();
}
function inlineStopPropagation(e) {
    e.stopPropagation();
    console.log("test")
}


function copyTextToClipboard(text) {
  if (!navigator.clipboard) {
    fallbackCopyTextToClipboard(text);
    return;
  }
  navigator.clipboard.writeText(text).then(function() {
      snackbarShow('Successfully copied free taster link', 'success')
  }, function(err) {
      snackbarShow('Failed to copy free taster link', 'danger')
  });
}

function fallbackCopyTextToClipboard(text) {
    var textArea = document.createElement("textarea");
    textArea.value = text;
    
    // Avoid scrolling to bottom
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";
  
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
  
    try {
      var successful = document.execCommand('copy');
      var msg = successful ? 'successful' : 'unsuccessful';
      if (msg == 'successful') {
        snackbarShow('Successfully copied free taster link', 'success')
      } else {
        snackbarShow('Failed to copy free taster link', 'danger')
      }
    } catch (err) {
    }
  
    document.body.removeChild(textArea);
}

