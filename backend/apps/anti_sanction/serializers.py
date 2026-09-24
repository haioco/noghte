from rest_framework import serializers
from apps.plans.models import Plan
from apps.subscriptions.models import Subscription


class PackageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='id', read_only=True)
    name = serializers.CharField(source='name', read_only=True)
    price = serializers.IntegerField(source='price_toman', read_only=True)

    class Meta:
        model = Plan
        fields = ['id', 'name', 'price', 'description', 'traffic_bytes', 'duration_days']


class AntiSanctionSubscriptionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source='uuid', read_only=True)
    title = serializers.CharField(read_only=True)
    package_id = serializers.IntegerField(source='plan.id', read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'title', 'package_id', 'status', 'username', 'created_at']


class CreateSubscriptionSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=30)
    package_id = serializers.IntegerField(min_value=1)


class ListSubscriptionSerializer(serializers.Serializer):
    filter = serializers.CharField(required=False, allow_blank=True)
    page = serializers.IntegerField(required=False, default=1, min_value=1)
