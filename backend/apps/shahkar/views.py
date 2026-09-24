from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .serializers import (
    VerifyIdentitySerializer, GetVerifyMobileSerializer, VerifyMobileSerializer
)


class VerifyIdentityView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = VerifyIdentitySerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Placeholder: actual Shahkar integration
        return Response({"message": "Verification code sent.", "token": serializer.validated_data['token']})


class VerifyIdentityResendView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        # Placeholder: actual Shahkar integration
        return Response({"message": "Verification code resent."})


class GetVerifyMobileView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = GetVerifyMobileSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"message": "OTP sent.", "mobile": serializer.validated_data['mobile']})


class VerifyMobileView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = VerifyMobileSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Placeholder: actual Shahkar integration
        return Response({"message": "Mobile verified successfully.", "mobile": serializer.validated_data['mobile']})
