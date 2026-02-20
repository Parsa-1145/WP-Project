from cases.submissiontypes import ComplaintSubmissionType, CrimeSceneSubmissionType, BaseSubmissionType, CaseStaffingSubmissionType

SUBMISSION_TYPES: dict[str, type[BaseSubmissionType]] = {
    ComplaintSubmissionType.type_key: ComplaintSubmissionType,
    CrimeSceneSubmissionType.type_key: CrimeSceneSubmissionType,
    CaseStaffingSubmissionType.type_key: CaseStaffingSubmissionType
}


SUBMISSION_TYPE_CHOICES = [
    (k, cls.display_name) for k, cls in SUBMISSION_TYPES.items()
]

def get_submission_type(key) -> type[BaseSubmissionType]:
    return SUBMISSION_TYPES[key]