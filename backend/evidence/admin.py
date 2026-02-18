from django.contrib import admin
from .models import Evidence, WitnessEvidence, BioEvidence, VehicleEvidence, IdentityEvidence, BioEvidenceImage, OtherEvidence

@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_type', 'title', 'created_at', 'case', 'recorder')
    search_fields = ('title', 'description')
    list_filter = ('created_at',)

    def get_type(self, obj):
        return obj.get_evidence_type_display()
    get_type.short_description = "Type"

    def has_add_permission(self, request):
        return False

@admin.register(WitnessEvidence)
class WitnessEvidenceAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'case', 'recorder', 'created_at',)
    search_fields = ('title', 'description', 'case__title')
    list_filter = ('created_at',)

    fieldsets = (
        ('General Information', {
            'fields': ('title', 'description', 'case', 'recorder')
        }),
        ('Witness Details', {
            'fields': ('media_file', 'transcript')
        })
    )

class BioEvidenceImageAdmin(admin.TabularInline): 
    model = BioEvidenceImage
    fk_name = 'evidence'
    extra = 1

@admin.register(BioEvidence)
class BioEvidenceAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'case', 'recorder', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('created_at',)

    fieldsets = (
        ('General Information', {
            'fields': ('title', 'description', 'case', 'recorder')
        }),
        ('Biological Details', {
            'fields': ('coroner_result', 'is_verified')
        })
    )

    inlines = [BioEvidenceImageAdmin]


@admin.register(VehicleEvidence)
class VehicleEvidenceAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'case', 'recorder', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('created_at',)

    fieldsets = (
        ('General Information', {
            'fields': ('title', 'description', 'case', 'recorder')
        }),
        ('Vehicle Details', {
            'fields': ('plate_number', 'serial_number', 'model_name', 'color')
        })
    )

@admin.register(IdentityEvidence)
class IdentityEvidenceAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'case', 'recorder', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('created_at',)

    fieldsets = (
        ('General Information', {
            'fields': ('title', 'description', 'case', 'recorder')
        }),
        ('Identity Details', {
            'fields': ('full_name', 'details')
        })
    )



@admin.register(OtherEvidence)
class OtherEvidenceAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'case', 'recorder', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('created_at',)

