from cases.submissiontypes import ComplaintSubmissionType, CrimeSceneSubmissionType, BaseSubmissionType
from evidence.submissiontypes import BioEvidenceSubmissionType

SUBMISSION_TYPES: dict[str, type[BaseSubmissionType]] = {
    ComplaintSubmissionType.type_key: ComplaintSubmissionType,
    CrimeSceneSubmissionType.type_key: CrimeSceneSubmissionType,
    BioEvidenceSubmissionType.type_key: BioEvidenceSubmissionType,
}


SUBMISSION_TYPE_CHOICES = [
    (k, cls.display_name) for k, cls in SUBMISSION_TYPES.items()
]

def get_submission_type(key) -> type[BaseSubmissionType]:
    return SUBMISSION_TYPES[key]