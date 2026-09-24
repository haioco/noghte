import uuid
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.plans.models import Plan
from apps.subscriptions.models import Subscription
from apps.subscriptions.services.anti_sanction import anti_sanction_client, generate_username, generate_password
from .serializers import (
    PackageSerializer, AntiSanctionSubscriptionSerializer,
    CreateSubscriptionSerializer, ListSubscriptionSerializer
)


class PackageListView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PackageSerializer

    def get_queryset(self):
        return Plan.objects.filter(is_active=True, is_visible=True)


class AntiSanctionListCreateView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AntiSanctionSubscriptionSerializer

    def get(self, request, *args, **kwargs):
        serializer_class = ListSubscriptionSerializer
        # List logic
        queryset = Subscription.objects.filter(user=request.user).select_related('plan')
        filter_param = request.query_params.get('filter')
        if filter_param == 'active':
            queryset = queryset.filter(status='active')
        page = request.query_params.get('page', 1)
        # For simplicity return all
        serializer = AntiSanctionSubscriptionSerializer(queryset, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = CreateSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        title = serializer.validated_data['title']
        package_id = serializer.validated_data['package_id']

        try:
            plan = Plan.objects.get(id=package_id, is_active=True, is_visible=True)
        except Plan.DoesNotExist:
            raise ValidationError("Package not found.")

        if plan.price_toman > 0 and user.profile.balance < plan.price_toman:
            raise ValidationError(
                f"Insufficient balance. Need {plan.price_toman} Toman, you have {user.profile.balance} Toman."
            )

        username = generate_username()
        password = generate_password()

        subscription = Subscription(
            uuid=uuid.uuid4(),
            user=user,
            plan=plan,
            title=title,
            status='pending',
            username=username,
            password=password,
        )
        subscription.save()

        resp = anti_sanction_client.add_user(username, password, plan.traffic_bytes)
        if not resp:
            raise ValidationError("Currently unable to activate Anti Sanction. Please try again later.")

        subscription.status = 'active'
        subscription.activated_at = timezone.now()
        subscription.save(update_fields=['status', 'activated_at'])

        if plan.price_toman > 0 and not user.profile.withdraw(plan.price_toman):
            subscription.delete()
            anti_sanction_client.remove_user(username)
            raise ValidationError("Balance deduction failed.")

        return Response(
            AntiSanctionSubscriptionSerializer(subscription).data,
            status=status.HTTP_201_CREATED,
        )


class AntiSanctionDetailView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AntiSanctionSubscriptionSerializer
    lookup_field = 'uuid'

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).select_related('plan')


class AntiSanctionRenewView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AntiSanctionSubscriptionSerializer
    lookup_field = 'uuid'

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).select_related('plan')

    @transaction.atomic
    def put(self, request, uuid, *args, **kwargs):
        subscription = self.get_object()
        user = request.user
        plan = subscription.plan

        if plan.price_toman > 0 and user.profile.balance < plan.price_toman:
            raise ValidationError(
                f"Insufficient balance. Need {plan.price_toman} Toman, you have {user.profile.balance} Toman."
            )

        if plan.price_toman > 0 and not user.profile.withdraw(plan.price_toman):
            raise ValidationError("Balance deduction failed.")

        now = timezone.now()
        needs_full_renew = (
            subscription.expired_at <= now
            or subscription.traffic_usage_byte >= subscription.total_traffic_byte
            or subscription.traffic_is_over
        )

        if needs_full_renew:
            subscription.total_traffic_byte = plan.traffic_bytes
            subscription.total_traffic_usage_byte = 0
            subscription.traffic_is_over = False
            subscription.status = 'active'
            subscription.expired_at = now + timedelta(days=plan.duration_days)
            subscription.save(update_fields=[
                'total_traffic_byte', 'total_traffic_usage_byte',
                'traffic_is_over', 'status', 'expired_at', 'updated_at',
            ])
            resp = anti_sanction_client.renew_user(
                subscription.username, subscription.password, plan.traffic_bytes
            )
            if not resp:
                raise ValidationError("Currently unable to renew Anti Sanction. Please try again later.")
        else:
            subscription.expired_at = now + timedelta(days=plan.duration_days)
            subscription.save(update_fields=['expired_at', 'updated_at'])

        return Response(
            AntiSanctionSubscriptionSerializer(subscription).data,
        )
