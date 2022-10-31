var PageTitleNotification = {
    Vars:{
        OriginalTitle: document.title,
        Interval: null
    },    
    On: function(notification, intervalSpeed){
        var _this = this;
        _this.Vars.Interval = setInterval(function(){
             document.title = (_this.Vars.OriginalTitle == document.title)
                                 ? notification
                                 : _this.Vars.OriginalTitle;
        }, (intervalSpeed) ? intervalSpeed : 1000);
    },
    Off: function(){
        clearInterval(this.Vars.Interval);
        document.title = this.Vars.OriginalTitle;   
    }
}

function clear_chat_from_session(customer_number){
    var respStatus = $.ajax({
        type:'POST',
        url:'{%url "clear-chat-from-session"%}',
        data:{'customer_number':customer_number, 'csrfmiddlewaretoken':'{{ csrf_token }}'},
        success: function (data) {
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
        }
    })
}

function add_chat_conversation_to_session(whatsappnumber_pk, customer_number){
        var respStatus = $.ajax({
            type:'POST',
            url:'{%url "add-chat-conversation-to-session"%}',
            data:{'whatsappnumber_pk':whatsappnumber_pk, 'customer_number':customer_number, 'csrfmiddlewaretoken':'{{ csrf_token }}'},
            success: function (data) {
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
            }
        })
}

function add_chat_whatsapp_number_to_session(whatsapp_number){
    var respStatus = $.ajax({
        type:'POST',
        url:'{%url "add-chat-whatsapp-number-to-session"%}',
        data:{'whatsapp_number':whatsapp_number, 'csrfmiddlewaretoken':'{{ csrf_token }}'},
        success: function (data) {
        },
        error: function(XMLHttpRequest, textStatus, errorThrown) {
        }
    })
}

function inlinePreventDefault(e) {
    e.preventDefault();
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