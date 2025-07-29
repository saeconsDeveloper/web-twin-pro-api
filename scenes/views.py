import json
import threading

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render
from django.views.generic import (CreateView, DeleteView, FormView, ListView,
                                  TemplateView, UpdateView, View)
from django.conf import settings

from rest_framework import status
from rest_framework.authentication import (BaseAuthentication,
                                           SessionAuthentication)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, Token
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError

from dashboard.models import *
from dashboard.permissions import *
from dashboard.utils import *
from two_factor_auth.utils import *

# from .mixins import *
from .utils import *
from dashboard.audits import store_audit
# from .serializers import *


class LoginView(APIView):

    permission_classes = []
    authentication_classes = []

    def post(self, request):
        body = json.loads(request.body)
        email = body['data']['email']
        password = body['data']['password']

        try:
            # username = User.objects.get(email__iexact=email).username
            user = authenticate(username=email, password=password)
        except Exception as e:
            user = None

        if user is not None:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            return Response({
                "response": 'user logged in',
                "tokens": {
                    "refresh_token": str(refresh),
                    "access_token": str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "message": "invalid credentials"
            },
                status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
        except Exception as e:
            return Response({"response": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        store_audit(request=request, instance=request.user, action="LOGOUT")
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception as e:
            return Response({'error':[str(e)]}, status=status.HTTP_400_BAD_REQUEST)
        
        logout(request)
                
        return Response({"success": "user logged out."}, status=status.HTTP_200_OK)
    # DELETE THE JWT


class ResetPasswordView(APIView):

    def post(self, request):
        email = request.data.get('email')
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user == None:
            return Response({
                "message": "this email does not exist."
            },
                status=status.HTTP_400_BAD_REQUEST)
        else:
            self.send_reset_mail(email)
            return Response({
                'message': 'password reset link sent'
            },
                status=status.HTTP_200_OK)

    def send_reset_mail(self, email):
        if not User.objects.filter(email__iexact=email).exists():
            return Response({
                'message': "email : {} was not found".format(email)
            },
                status=status.HTTP_400_BAD_REQUEST
            )
        user = User.objects.filter(email__iexact=email).first()

        t = threading.Thread(target=send_reset_mail_for_email, args=(user, ))
        t.start()
        return Response({"message": "reset password e-mail sent"}, status=status.HTTP_200_OK)


class SetNewPasswordView(APIView):

    def get_user(self):
        if not hasattr(self, '__user') or self.__user == None:
            self.__user = get_user_from_tokens(
                idx=self.kwargs['idx'], token=self.kwargs['token'])
        return self.__user

    def post(self, request, *args, **kwargs):
        pass1 = request.data.get('pass1')
        pass2 = request.data.get('pass2')
        if (pass1 or pass2) is None:
            return Response({
                'message': 'no password found'
            },
                status=status.HTTP_400_BAD_REQUEST)
        elif pass1 != pass2:
            return Response({
                'message': 'passwords donot match'
            },
                status=status.HTTP_400_BAD_REQUEST)
        else:
            user = self.get_user()
            user.set_password(pass1)
            user.save()
            return Response({
                'message': 'password set successfully'
            },
                status=status.HTTP_200_OK)

# ---------------------------------------------------------------------------------------------------------
# SCENES POSITION
# ---------------------------------------------------------------------------------------------------------


class ScenePositionUpdateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [SuperAdminPermission | UberAdminPermission]

    def get(self, request, *args, **kwargs):
        body = json.loads(request.body)
        try:
            scene = body['data']['scene']
            id = body['data']['id']
            top = body['data']['top']
            left = body['data']['left']
            if scene and id and top and left:
                if ProductTier1Position.objects.filter(
                    scene_id=int(scene), product_tier_1_id=id
                ).exists():
                    service_position = ProductTier1Position.objects.filter(
                        scene_id=int(scene), product_tier_1_id=id
                    ).first()
                else:
                    service_position = ProductTier1Position(
                        scene_id=int(scene), product_tier_1_id=id
                    )
                service_position.position_x = int(float(left))
                service_position.position_y = int(float(top))
                service_position.save()
            return Response({"message": "success"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": "error", "not found": str(e)}, status=status.HTTP_400_BAD_REQUEST)
