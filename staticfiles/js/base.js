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
    let status = evt.detail.xhr.status;
    let srcElement = $(evt.srcElement);
    let src_id = srcElement.attr('id');
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
                OriginalTitle = document.title;
                PageTitleNotification.On("Message Sent/Received!", 1000);         
                setTimeout(function() {
                    PageTitleNotification.Off();
                }, 2000);
            }
        }
    } else if (status == 404) {
        if ($('#'+src_id+"_error").length == 0){                                
            $("#"+src_id).after("<div id='"+src_id+"_error' style='color:red'>Not Found</div>");
        } else {                                
            $('#'+src_id+"_error").html("<div id='"+src_id+"_error' style='color:red'>Not Found</div>");
        }
    }else if (status == 500){
        snackbarShow('Error: '+evt.detail.xhr.response, 'danger')           
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

function clear_chat_from_session(customer_number){
    var respStatus = $.ajax({
        type:'POST',
        url:'/ajax-clear-chat-from-session/',
        data:{'customer_number':customer_number, 'csrfmiddlewaretoken':csrftoken},
        success: function (data) {
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
        }
    })
}

function add_chat_conversation_to_session(whatsappnumber_pk, customer_number){
        var respStatus = $.ajax({
            type:'POST',
            url:'/ajax-add-chat-conversation-to-session/',
            data:{'whatsappnumber_pk':whatsappnumber_pk, 'customer_number':customer_number, 'csrfmiddlewaretoken':csrftoken},
            success: function (data) {
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
            }
        })
}

function add_chat_whatsapp_number_to_session(whatsapp_number){
    var respStatus = $.ajax({
        type:'POST',
        url:'/ajax-add-chat-whatsapp-number-to-session/',
        data:{'whatsapp_number':whatsapp_number, 'csrfmiddlewaretoken':csrftoken},
        success: function (data) {
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
        }
    })
}

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

