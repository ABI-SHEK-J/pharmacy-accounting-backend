from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth import authenticate

from rest_framework_simplejwt.tokens import RefreshToken


@api_view(['POST'])
def login_view(request):

    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user is not None:

        refresh = RefreshToken.for_user(user)

        return Response({
            'status': True,
            'message': 'Login Success',

            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),

            'user': {
                'id': user.id,
                'username': user.username,
            }

        })

    return Response({
        'status': False,
        'message': 'Invalid Username or Password'
    }, status=status.HTTP_401_UNAUTHORIZED)