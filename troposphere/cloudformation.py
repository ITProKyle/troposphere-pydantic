"""AWS CloudFormation CloudFormation.

https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/AWS_CloudFormation.html

"""
# pylint: disable=no-self-argument,no-self-use
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import Field, root_validator

from . import AWSHelperFnOrDict, AWSObject, policies


class WaitCondition(AWSObject):
    """AWS::CloudFormation::WaitCondition resource."""

    RESOURCE_TYPE = "AWS::CloudFormation::WaitCondition"

    Count: Optional[int] = None
    Handle: Optional[AWSHelperFnOrDict] = None
    Timeout: Optional[int] = Field(default=None, le=43200)

    CreationPolicy: Optional[policies.CreationPolicy] = None

    @root_validator(pre=True)
    def _validate_fields(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate fields."""
        conditionally_required = {k: values.get(k, None) for k in ["Handle", "Timeout"]}
        if values.get("CreationPolicy", None):
            for k, v in conditionally_required.items():
                if v:
                    raise ValueError(
                        f"Property {k} cannot be specified with CreationPolicy"
                    )
        else:
            for k, v in conditionally_required.items():
                if not v:
                    raise ValueError(
                        f"{k} field required when not specifying CreationPolicy"
                    )
        return values


class WaitConditionHandle(AWSObject):
    """AWS::CloudFormation::WaitConditionHandle resource."""

    RESOURCE_TYPE = "AWS::CloudFormation::WaitConditionHandle"
