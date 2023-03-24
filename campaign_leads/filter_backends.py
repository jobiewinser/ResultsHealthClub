from rest_framework_datatables.filters import DatatablesFilterBackend

class DefineSearchFieldsDatatablesBaseFilterBackend(DatatablesFilterBackend):
    def get_fields(self, request):
        # return ['site_contact__first_name','site_contact__last_name']
        return [
            {
                'name': ['site_contact__first_name', 'site_contact__last_name'], 
                'data': ['site_contact__first_name', 'site_contact__last_name'], 
                'searchable': True, 
                'orderable': True, 
                'search_value': '', 
                'search_regex': False
            },            
            {
                'name': ['site_contact__last_name'], 
                'data': 'site_contact__last_name', 
                'searchable': True, 
                'orderable': True, 
                'search_value': '', 
                'search_regex': False
            },            
            {
                'name': ['campaign__name'], 
                'data': 'campaign__name', 
                'searchable': True, 
                'orderable': True, 
                'search_value': '', 
                'search_regex': False
            },            
            {
                'name': ['product_cost'], 
                'data': 'product_cost', 
                'searchable': True, 
                'orderable': True, 
                'search_value': '', 
                'search_regex': False
            },            
            {
                'name': ['booking__datetime'], 
                'data': 'booking__datetime', 
                'searchable': True, 
                'orderable': True, 
                'search_value': '', 
                'search_regex': False
            }
        ]
    