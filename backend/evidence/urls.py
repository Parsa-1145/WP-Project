from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'', EvidenceListViewSet, basename='evidence')
router.register(r'witness', WitnessEvidenceViewSet, basename='witnessevidence')
router.register(r'bio', BioEvidenceViewSet, basename='bioevidence')
router.register(r'vehicle', VehicleEvidenceViewSet, basename='vehicleevidence')
router.register(r'identity', IdentityEvidenceViewSet, basename='identityevidence')


urlpatterns = [
    
]

urlpatterns += router.urls