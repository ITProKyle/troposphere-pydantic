"""Policies.

NOTE: Not IAM policies.

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, cast

from pydantic import Field, validator

from . import AWSAttribute, AWSProperty
from .validators import validate_pause_time

if TYPE_CHECKING:
    from typing import Any, Callable


class ResourceSignal(AWSProperty):
    """:attr:`CreationPolicy.ResourceSignal`."""

    Count: Optional[int] = Field(default=None, gt=0)
    Timeout: Optional[str]

    _validate_pause_time = cast(
        "classmethod[Callable[..., Any]]",
        validator("Timeout", allow_reuse=True)(validate_pause_time),
    )


class AutoScalingCreationPolicy(AWSProperty):
    """:attr:`CreationPolicy.AutoScalingCreationPolicy`."""

    MinSuccessfulInstancesPercent: Optional[int] = None


class CreationPolicy(AWSAttribute):
    """Resource attribute.

    https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-attribute-creationpolicy.html

    """

    AutoScalingCreationPolicy: Optional[AutoScalingCreationPolicy] = None
    ResourceSignal: ResourceSignal
