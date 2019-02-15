from rest_framework.pagination import PageNumberPagination


#商品分页配置类
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = 'page_size'
    max_page_size = 20