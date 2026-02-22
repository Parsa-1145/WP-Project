from rest_framework import permissions
from cases.models import Case
from .models import DetectiveBoard


class IsDetectiveBoardOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a detective board to edit it.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not request.user.has_perm('cases.investigate_on_case'):
            return False
        
        return True

    def has_object_permission(self, request, view, obj):
        
        if isinstance(obj, DetectiveBoard):
            if request.user.has_perm('cases.view_all_cases'):
                return True
            
            return obj.case.assigned_detectives.filter(id=request.user.id).exists()
        
        return True