function renderTemplate(){
    console.log("renderTemplate")
    let content = ""
    if ($('#template_header').val() != "") {
        content = replaceVariables("<b>"+$('#template_header').val()+"</b> <br><br>  ")
    }
    if ($('#template_body').val() != "") {
        content = content + replaceVariables("<p>"+$('#template_body').val().replace(/\r\n|\r|\n/g,"<br />")+"</p>")
    }
    if ($('#template_footer').val() != "") {
        content = content + "<small>"+$('#template_footer').val()+"</small>"  
    }
    
    $('#template_render').html(content)
}
function replaceVariables(content){
    for (const [k,v] of Object.entries(variables)){
        content = content.replaceAll(k, v[1])
    }
    return content
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
                $('#page_load_indicator').removeClass('htmx-request')
                htmx.ajax('GET', '/configuration/whatsapp-templates/', {target:'#content'})
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                $('#page_load_indicator').removeClass('htmx-request')
            }
        })
    } else {
        alert('Your template contains some invalid characters ( "{" or "}" ). Replace any "{{x}}" variables with properly entered variables.')
    }
}