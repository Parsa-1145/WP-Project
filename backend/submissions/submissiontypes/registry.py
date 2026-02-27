from cases.submissiontypes import ComplaintSubmissionType, GuiltAssesmentSubmissionType, CrimeSceneSubmissionType, BaseSubmissionType, CaseStaffingSubmissionType, InvestigationResultsApprovalSubmissionType
from evidence.submissiontypes import BioEvidenceSubmissionType
from payments.submissiontypes import BailRequestSubmissionType, DataForRewardSubmissionType

SUBMISSION_TYPES: dict[str, type[BaseSubmissionType]] = {
    ComplaintSubmissionType.type_key: ComplaintSubmissionType,
    CrimeSceneSubmissionType.type_key: CrimeSceneSubmissionType,
    CaseStaffingSubmissionType.type_key: CaseStaffingSubmissionType,
    InvestigationResultsApprovalSubmissionType.type_key: InvestigationResultsApprovalSubmissionType,
    BioEvidenceSubmissionType.type_key: BioEvidenceSubmissionType,
    GuiltAssesmentSubmissionType.type_key: GuiltAssesmentSubmissionType,
    BailRequestSubmissionType.type_key: BailRequestSubmissionType,
    DataForRewardSubmissionType.type_key: DataForRewardSubmissionType,
}


SUBMISSION_TYPE_CHOICES = [
    (k, cls.display_name) for k, cls in SUBMISSION_TYPES.items()
]

def get_submission_type(key) -> type[BaseSubmissionType]:
    return SUBMISSION_TYPES[key]