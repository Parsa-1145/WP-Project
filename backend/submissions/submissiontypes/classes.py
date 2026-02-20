from typing import ClassVar, Type
from rest_framework.serializers import Serializer, DictField
from django.db.models import Model
from typing import ClassVar, Generic, Type, TypeVar
from accounts.models import User
from submissions.models import Submission, SubmissionAction, SubmissionStage
from drf_spectacular.utils import inline_serializer, OpenApiExample
from rest_framework.exceptions import ValidationError

TModel = TypeVar("TModel", bound=Model)


class BaseSubmissionType(Generic[TModel]):
    type_key:                       ClassVar[str]
    display_name:                   ClassVar[str]
    serializer_class:               ClassVar[Type[Serializer]]  
    model_class:                    ClassVar[Type[TModel]]
    create_permissions:             ClassVar[list[str]]                = []
    api_request_schema:             ClassVar[Type[Serializer] | None]  = DictField(required=True)
    api_request_payload_example:    ClassVar[dict | None]              = {} 
    api_response_target_example:    ClassVar[dict | None]              = {} 
    can_be_created_from_request:    ClassVar[bool]                     = True         

    @classmethod
    def can_user_submit(cls, user: User) -> bool:
        if not cls.can_be_created_from_request:
            return False
        if not user or not user.is_authenticated:
            return False
        if not cls.create_permissions:
            return True
        return user.has_perms(cls.create_permissions)
    
    @classmethod
    def can_user_do_action(cls, submission: Submission, user: User) -> bool:
        stage = SubmissionStage.objects.filter(submission=submission, order=submission.current_stage).first()
        if not stage:
            return True
        
        return (stage.target_user and stage.target_user == user) or (stage.target_permission and user.has_perm(stage.target_permission))

    @classmethod
    def validate_submission_data(cls, data, context) -> Serializer:
        if not cls.serializer_class:
            raise ValidationError({"submission_type": "Unsupported submission type: " + cls.type_key})
        
        serializer = cls.serializer_class(
            data=data,
            context=context
        )
        serializer.is_valid(raise_exception=True)
        return serializer

    @classmethod
    def on_submit(cls, submission: Submission) -> None:
        """
        Called when a submission is first created
        """
        pass

    @classmethod
    def handle_submission_action(cls, submission: Submission, action: SubmissionAction, context, **kwargs):
        """
        Called when an action happens on a submission
        
        :param context: The context in which the action happend
        """
        pass

    @classmethod
    def validate_submission_action_payload(cls, submission, action_type, payload, context, **kwargs):
        """
        Validate the action payload. called before evry action.
        
        :param context: The context in which the action happend
        """
        pass

    @classmethod
    def get_object(cls, object_id) -> TModel:
        """
        Get the target object of the submission
        
        :param object_id: The object_id of the submission target
        :return: Submission target
        :rtype: TModel
        """
        return cls.model_class._default_manager.get(pk=object_id)
    
    @classmethod
    def create_object(cls, payload, context):
        """
        Create the submission target object from the payload
        """

        serializer = cls.serializer_class(
            data=payload,
            context=context
        )

        serializer.save()