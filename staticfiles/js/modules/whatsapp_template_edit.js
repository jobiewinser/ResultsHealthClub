function renderTemplate(){
    console.log("renderTemplate")
    let content = ""

    let template_header = $('#template_header').val();
    let template_body = $('#template_body').val();
    let template_footer = $('#template_footer').val();

    if (template_header != "") {
        content = replaceVariables("<b>"+template_header+"</b> <br><br>")
    }
    if (template_body != "") {
        content = content + replaceVariables("<p>"+template_body.replace(/\r\n|\r|\n/g,"<br />")+"</p>")
    }
    if (template_footer != "") {
        content = content + "<small>"+template_footer+"</small>"  
    }

    $('#variable2_warning').prop('hidden', template_header.indexOf('[[2]]') == -1 && template_body.indexOf('[[2]]') == -1 && template_footer.indexOf('[[2]]') == -1);
    
    
    $('#template_render').html(content)
}


function replaceVariables(content){
    for (const [k,v] of Object.entries(variables)){
        content = content.replaceAll(k, v[1])
    }
    return content
}
function validateWhatsappText(elem){
    let value = elem.value.replaceAll(" ", "_").toLowerCase()
    value = value.replace(/[^a-z_]/, '');
    elem.value = value
}
function saveTemplate(whatsapp_business_account_pk, template_pk, create=false){
    var variables_valid = true;
    let header = $('#template_header').val();
    let body = $('#template_body').val();
    let footer = $('#template_footer').val();
    for (const text of [header, body, footer]){
        if (text.indexOf('{') !== -1 || text.indexOf('}') !== -1){
            variables_valid = false;
        }
    }
    let post_data = {};
    
    if (create == true) {
        post_data = {
            'created':true,
            'name':$('#template_name').val(), 
            'category':$('#template_category').val(), 
            'header':$('#template_header').val(), 
            'body':$('#template_body').val(), 
            'whatsapp_business_account_pk':whatsapp_business_account_pk, 
            'footer':$('#template_footer').val(), 
            'csrfmiddlewaretoken':csrftoken
        }
    } else {
        post_data = {
            'template_pk':template_pk,
            'name':$('#template_name').val(), 
            'category':$('#template_category').val(), 
            'header':header, 
            'body':body, 
            'footer':footer, 
            'csrfmiddlewaretoken':csrftoken
        }
    }
    if (variables_valid){
        $('#page_load_indicator').addClass('htmx-request')
        var respStatus = $.ajax({
            type:'POST',
            url:'/configuration/whatsapp-templates-save/',
            data: post_data,
            success: function (data) {
                $(window).unbind('beforeunload');         
                window.history.pushState("Whatsapp Templates", "Title", "/configuration/whatsapp-templates/");
                htmx.ajax('GET', "/configuration/whatsapp-templates/", {indicator:'#page_load_indicator', swap:'innerHTML', target: '#content'})
                $('#page_load_indicator').removeClass('htmx-request')
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                $('#page_load_indicator').removeClass('htmx-request')
            }
        })
    } else {
        alert('Your template contains some invalid characters ( "{" or "}" ). Replace any "{{x}}" variables with properly entered variables.')
    }
}