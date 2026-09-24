from rest_framework import serializers


class VerifyIdentitySerializer(serializers.Serializer):
    token = serializers.CharField(required=True)


class GetVerifyMobileSerializer(serializers.Serializer):
    mobile = serializers.CharField(required=True, max_length=15)


class VerifyMobileSerializer(serializers.Serializer):
    mobile = serializers.CharField(required=True, max_length=15)
    token = serializers.CharField(required=True, max_length=10)
