from django.urls import path
from .views import (
    VerifyIdentityView, VerifyIdentityResendView,
    GetVerifyMobileView, VerifyMobileView,
)

urlpatterns = [
    path('user/verify/identity', VerifyIdentityView.as_view(), name='verify-identity'),
    path('user/verify/identity/resend', VerifyIdentityResendView.as_view(), name='verify-identity-resend'),
    path('user/getVerifyMobile', GetVerifyMobileView.as_view(), name='get-verify-mobile'),
    path('user/verifyMobile', VerifyMobileView.as_view(), name='verify-mobile'),
]
