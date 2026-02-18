from typing import ClassVar, Type
from rest_framework.serializers import Serializer
from django.db.models import Model
from typing import ClassVar, Generic, Type, TypeVar
from accounts.models import User
from submissions.models import Submission, SubmissionAction

TModel = TypeVar("TModel", bound=Model)


class BaseSubmissionType(Generic[TModel]):
    type_key: ClassVar[str]
    display_name: ClassVar[str]
    serializer_class: ClassVar[type[Serializer]]
    model_class: ClassVar[type[TModel]]
    create_permissions: ClassVar[list[str]] = []

    @classmethod
    def does_user_have_access(cls, user: User) -> bool:
        if not user or not user.is_authenticated:
            return False
        if not cls.create_permissions:
            return True
        return user.has_perms(cls.create_permissions)

    @classmethod
    def validate_submission_data(cls, data, context):
        serializer = cls.serializer_class(
            data=data,
            context=context
        )
        serializer.is_valid(raise_exception=True)
        return serializer

    @classmethod
    def on_submit(cls, submission: Submission) -> None:
        pass

    @classmethod
    def handle_submission_action(cls, submission_obj, action: SubmissionAction, context, **kwargs):
        pass

    @classmethod
    def get_object(cls, object_id) -> TModel:
        return cls.model_class._default_manager.get(pk=object_id)
    