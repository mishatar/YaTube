from django.core.paginator import Paginator

CONST = 10


def paginator_func(queryset, request):
    paginator = Paginator(queryset, CONST)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
