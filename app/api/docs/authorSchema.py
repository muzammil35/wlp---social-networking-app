from drf_yasg import openapi

AUTHOR_LIST_REGISTER_REQUEST_BODY = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'displayName': openapi.Schema(type=openapi.TYPE_STRING, description='Display name of the author'),
        'username': openapi.Schema(type=openapi.TYPE_STRING, description='username of the author for authentication'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, description='username of the author for authentication'),
        'github': openapi.Schema(type=openapi.TYPE_STRING, description='github url of the author'),
        'profileImage': openapi.Schema(type=openapi.TYPE_STRING, description='profile image url of the author'),
    })

AUTHOR_DETAIL_UPDATE_REQUEST_BODY = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'github': openapi.Schema(type=openapi.TYPE_STRING, description='github url of the author'),
        'profileImage': openapi.Schema(type=openapi.TYPE_STRING, description='profile image url of the author'),
    })
