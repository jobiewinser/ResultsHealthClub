from django.http import HttpResponse


def get_sales(request):
    return HttpResponse("test", status=200)