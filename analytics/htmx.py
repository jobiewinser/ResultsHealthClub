from django.http import HttpResponse
from django.shortcuts import render

def get_leads_to_sales(request):
    context = {}
    data = []
    for data_entry in [1,2,3]:
        leads = 5
        sales = 2  
        data.append({'leads':leads,'sales':sales,'percentage':(sales/leads)*100})
    context['dataset'] = {
        'months':[4,5,6], 
        'data': data
        
    }
    return render(request, 'analytics/htmx/leads_to_sale.html', context)