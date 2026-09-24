from django.urls import path
from .views import (
    PackageListView, AntiSanctionListCreateView,
    AntiSanctionDetailView, AntiSanctionRenewView,
)

urlpatterns = [
    path('anti/sanction/packages', PackageListView.as_view(), name='anti-sanction-packages'),
    path('anti/sanction', AntiSanctionListCreateView.as_view(), name='anti-sanction-list-create'),
    path('anti/sanction/<uuid:uuid>/', AntiSanctionDetailView.as_view(), name='anti-sanction-detail'),
    path('anti/sanction/<uuid:uuid>/renew/', AntiSanctionRenewView.as_view(), name='anti-sanction-renew'),
]
