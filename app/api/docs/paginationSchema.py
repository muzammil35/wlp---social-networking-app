from drf_yasg import openapi

PAGE_PARAMETER = openapi.Parameter('page', openapi.IN_QUERY,
                                   description="Page number. Default is 1",
                                   type=openapi.TYPE_INTEGER)

SIZE_PARAMETER = openapi.Parameter('size', openapi.IN_QUERY,
                                   description="Number of objects per page. Default is 20",
                                   type=openapi.TYPE_INTEGER)
