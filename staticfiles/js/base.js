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
    if (evt.detail.target.id == 'content'){
        $('#generic_modal').modal('hide');
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
}
// var tapped=false

// function setDoubleTap(identifier){
    // $(identifier).on("touchstart",function(e){
//         if(!tapped){ //if tap is not set, set up single tap
//             tapped=setTimeout(function(){
//                 tapped=null
//                 //insert things you want to do when single tapped
//             },300);   //wait 300ms then run single click code
//         } else {    //tapped within 300ms of last tap. double tap
//           clearTimeout(tapped); //stop single tap callback
//           tapped=null
//           htmx.ajax('GET', '/toggle-claim-lead/'+$(e.currentTarget).data('id')+'/', {swap:"none"})
//         }
//         e.preventDefault()
    // });
// }

function setDoubleTap(identifier){
    var tapedTwice = false;
    $(identifier).on("touchstart",function(e){
        if(!tapedTwice) {
            tapedTwice = true;
            setTimeout( function() { tapedTwice = false; }, 300 );
            return false;
        }
        event.preventDefault();
        htmx.ajax('GET', '/toggle-claim-lead/'+$(e.currentTarget).data('id')+'/', {swap:"none"})
    });
    
}

function select2stuff(){
    $('.select2:not([data-select2-id])').select2({
        searchInputPlaceholder: '🔎 Search here...',        
        theme: 'bootstrap-5',
    })
    
    $('.generic_modal_body_select').select2({
        dropdownCssClass: "generic_modal_body_dropdown",
        dropdownParent: $("#generic_modal"),
        // searchInputPlaceholder: '🔎 Search here...',        
        // theme: 'bootstrap-5',
      });

    $('.select2tag:not([data-select2-id])').select2({     
        tags: true,
        createTag: function (tag) {
            return {id: tag.term, text: tag.term, tag: true};
        }
    })
    $('.select2tag').on('select2:open', function (e) {
        const evt = "scroll.select2";
        $(e.target).parents().off(evt);
        $(window).off(evt);
    });
}

function popoverstuff(){
    $("[data-toggle='popover']").popover('destroy');
    $(".popover").remove();    
    $('[data-bs-toggle=popover]').popover({
        animation:false
    });
}

function basehandlehtmxafterSettle(evt){ 
    var current_module = $('#current_page').val()
    if (current_module != 'campaign_booking_overview'){
        select2stuff()
        // flash()   
        popoverstuff()
    }
}

function basehandlehtmxafterRequest(evt){   
    // flash()   
    popoverstuff()
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
                $('#generic_modal').modal('hide');
                snackbarShow('Successfully logged in', 'success');
                $('#page_load_indicator').addClass('htmx-request')
                location.reload();
            }else if (evt.detail.pathInfo.requestPath.includes("modify-user")){
                $('#generic_modal').modal('hide');
                snackbarShow('Successfully added/modified profile', 'success');
                $('#page_load_indicator').addClass('htmx-request')
                location.reload();
            // }else if (evt.detail.pathInfo.requestPath.includes("add-stripe-payment-method")){
            //     $('#generic_modal').modal('hide');
            //     // snackbarShow('Successfully added/modified profile', 'success');
            //     $('#payment_methods_htmx_indicator').addClass('htmx-request')
            //     location.reload();                
            }else if (evt.detail.pathInfo.requestPath.includes("deactivate-profile")){
                $('#generic_modal').modal('hide');
                snackbarShow('Successfully deactivated profile', 'success');
                $('#page_load_indicator').addClass('htmx-request')
                location.reload();               
            }else if (evt.detail.pathInfo.requestPath.includes("reactivate-profile")){
                $('#generic_modal').modal('hide');
                snackbarShow('Successfully reactivated profile', 'success');
                $('#page_load_indicator').addClass('htmx-request')
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
            }else if (evt.detail.pathInfo.requestPath.includes("edit-lead")){
                $('#generic_modal').modal('hide');
                snackbarShow('Successfully changed/created a campaign lead', 'success')
                var current_module = $('#current_page').val()
                if (current_module == 'campaign_booking_overview'){
                    htmx.ajax('GET', "/refresh-booking-row/"+evt.detail.xhr.response+"/", {swap:'innerHTML', target: '#row_'+evt.detail.xhr.response})
                }
            }else if (evt.detail.pathInfo.requestPath.includes("add-campaign-category")){
                $('#generic_modal').modal('hide');
                snackbarShow('Successfully added a campaign category, reloading...', 'success')
                $('#page_load_indicator').addClass('htmx-request')
                location.reload();
            }else if (evt.detail.pathInfo.requestPath.includes("submit-feedback-form")){
                $('#generic_modal').modal('hide');
                snackbarShow('Successfully submitted feedback', 'success')
            } else if (evt.detail.pathInfo.requestPath.includes("import-active-campaign-leads")){
                $('#generic_modal').modal('hide');
                snackbarShow(evt.detail.xhr.responseText, 'success')
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
    }else if (status == 403){
        snackbarShow('You are not permitted to perform this action: '+evt.detail.xhr.response, 'danger', display_ms=5000)           
    }
}

function basehandlehtmxoobAfterSwap(evt){
    // flash()   
    popoverstuff()
    if ($(evt.detail.target).hasClass('chat_card_body')){                        
        $(evt.detail.target).animate({
            scrollTop: $(evt.detail.target)[0].scrollHeight - $(evt.detail.target)[0].clientHeight
        }, 100);
    }
}

function basehandlehtmxoobBeforeSwap(evt){    
    if ($(evt.target).hasClass('message_list_body')){
        htmx.ajax('GET', "/update-message-counts/", {swap:'none'})
    }
}



function isCalendlyEvent(e) {
    return e.origin === "https://calendly.com" && e.data.event && e.data.event.indexOf("calendly.") === 0;
};

function inlinePreventDefault(event) {
    event.preventDefault();
}
function inlineStopPropagation(event) {
    event.stopPropagation();
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

try{
    (function($) {

        var Defaults = $.fn.select2.amd.require('select2/defaults');

        $.extend(Defaults.defaults, {
            searchInputPlaceholder: ''
        });

        var SearchDropdown = $.fn.select2.amd.require('select2/dropdown/search');

        var _renderSearchDropdown = SearchDropdown.prototype.render;

        SearchDropdown.prototype.render = function(decorated) {

            // invoke parent method
            var $rendered = _renderSearchDropdown.apply(this, Array.prototype.slice.apply(arguments));

            this.$search.attr('placeholder', this.options.get('searchInputPlaceholder'));

            return $rendered;
        };

    })(window.jQuery);
}catch{}



// function flash() {
//     // try{
//         setTimeout(function(){
//         $('.flashme').each(function(flash) {
//             console.log("test")
//             $(flash).css('animation', '2s flash infinite');
//             $(flash).removeClass('flashme');
//             setTimeout(function(){
//                 try{
//                     $(flash).css('animation', 'unset');
//                 }catch{}
//             }, 2000); 
//         });
//     }, 100); 
//     // }catch{}
// }
// Output selected rows
function outputSubscriptionProfileChoice(site_subscription_change_pk) {
    // if (selectedRows.length == 0) {
    //   alert("No rows selected!");
    //   return;
    // }
    var submission_dict = {};
    $('.profile_choice_select').each(function(){
        if ($(this).is(':checked')) {
            submission_dict[$(this).attr('name')] = $(this).val();
        }        
    });
    submission_dict['site_subscription_change_pk'] = site_subscription_change_pk
    htmx.ajax('POST', '/choose-attached-profiles/', {target:'#generic_modal_body', swap:'innerHTML', values:submission_dict})
}