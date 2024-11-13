
from rest_framework.response import Response
from rest_framework import pagination, status


class CustomPagination(pagination.PageNumberPagination):
    page_size = 20
    page_size_query_param = 'size'

    def get_paginated_response(self, data):
        if data["type"] == "comments":
            return Response(
                {
                    "type": data["type"],
                    "items": data["comments"],
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "type": data["type"],
                "items": data["items"],
            },
            status=status.HTTP_200_OK,
        )
