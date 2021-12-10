"""Troposphere."""
# pylint: disable=no-self-argument,no-self-use,wrong-import-position
# caused by pending pydantic release
# pylint: disable=no-member,unsupported-assignment-operation,unsupported-membership-test
# pylint: disable=unsubscriptable-object
from __future__ import annotations

import json
import sys
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    ClassVar,
    Dict,
    Iterator,
    List,
    Mapping,
    NoReturn,
    Optional,
    Tuple,
    Type,
    TypedDict,
    TypeVar,
    Union,
    cast,
    overload,
)

import cfn_flip
from pydantic import BaseModel, Extra, Field, validator

from . import mixins, validators
from .constants import (
    MAX_MAPPINGS,
    MAX_OUTPUTS,
    MAX_PARAMETERS,
    MAX_RESOURCES,
    PARAMETER_TITLE_MAX,
    SERVERLESS_TRANSFORM,
)

if TYPE_CHECKING:
    from pydantic.fields import ModelField

    from .protocols import ToDictProtocol

if sys.version_info < (3, 8):
    # importlib.metadata is standard lib for python>=3.8, use backport
    from importlib_metadata import PackageNotFoundError
    from importlib_metadata import (
        version as get_version,  # type: ignore # pylint: disable=E
    )
else:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import (
        version as get_version,  # type: ignore # pylint: disable=E
    )

try:
    __version__ = get_version(__name__)
except PackageNotFoundError:
    # package is not installed
    __version__ = "0.0.0"


# constants for DeletionPolicy and UpdateReplacePolicy
Delete = "Delete"  # pylint: disable=invalid-name
Retain = "Retain"  # pylint: disable=invalid-name
Snapshot = "Snapshot"  # pylint: disable=invalid-name

# Pseudo Parameters
AWS_ACCOUNT_ID = "AWS::AccountId"
AWS_NOTIFICATION_ARNS = "AWS::NotificationARNs"
AWS_NO_VALUE = "AWS::NoValue"
AWS_PARTITION = "AWS::Partition"
AWS_REGION = "AWS::Region"
AWS_STACK_ID = "AWS::StackId"
AWS_STACK_NAME = "AWS::StackName"
AWS_URL_SUFFIX = "AWS::URLSuffix"

_T = TypeVar("_T")


# type aliases
AbstractSetIntStr = AbstractSet[Union[int, str]]
MappingIntStrAny = Mapping[Union[int, str], Any]


BaseAWSObjectType = TypeVar("BaseAWSObjectType", bound="BaseAWSObject")


def encode_to_dict(
    obj: Union[Dict[str, object], List[object], Tuple[object], object]
) -> Any:
    """Encode objects to dict."""
    if hasattr(obj, "to_dict"):
        # Calling encode_to_dict to ensure object is
        # nomalized to a base dictionary all the way down.
        return encode_to_dict(cast("ToDictProtocol", obj).to_dict())
    if isinstance(obj, (list, tuple)):
        new_lst: List[object] = []
        for i in cast(Union[List[object], Tuple[object, ...]], obj):
            new_lst.append(encode_to_dict(i))
        return new_lst
    if isinstance(obj, dict):
        props: Dict[str, object] = {}
        for name, prop in cast(Dict[str, object], obj).items():
            props[name] = encode_to_dict(prop)
        return props
    # This is useful when dealing with external libs using
    # this format. Specifically awacs.
    if hasattr(obj, "JSONrepr"):
        return encode_to_dict(obj.JSONrepr())  # type: ignore
    return obj


class BaseAWSObject(BaseModel):
    """Base class for AWS objects."""

    ATTRIBUTES: ClassVar[List[str]] = [
        "Condition",
        "CreationPolicy",
        "DeletionPolicy",
        "DependsOn",
        "Metadata",
        "UpdatePolicy",
        "UpdateReplacePolicy",
    ]
    DICT_NAME: ClassVar[Optional[str]] = None

    title: str = Field(..., regex=r"^[a-zA-Z0-9]+$")
    template: Optional[Template] = Field(default=None)

    class Config:
        """Model configuration."""

        arbitrary_types_allowed = True
        extra = Extra.forbid
        fields = {"template": {"exclude": True}, "title": {"exclude": True}}

    def __init__(self, **data: Any) -> None:
        """Instantiate class.

        Calls parent ``.__init__()`` method then performes custom steps.

        """
        super().__init__(**data)
        self.add_to_template()

    def add_to_template(self):
        """Add object to a Template.

        Called when outputting to dict.

        """
        if self.template:
            self.template.add_resource(self)

    def dict(
        self,
        *,
        include: Union[AbstractSetIntStr, MappingIntStrAny] = None,
        exclude: Union[AbstractSetIntStr, MappingIntStrAny] = None,
        by_alias: bool = False,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> Dict[str, Any]:
        """Generate a dictionary representation of the model.

        Wraps method from parent with additional value resolution and formatting
        specific to this usage.

        """
        data = super().dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
        if self.DICT_NAME:
            attributes = {}
            for attr in self.ATTRIBUTES:
                if attr in data:
                    attributes[attr] = data.pop(attr)
            return {self.DICT_NAME: data, **attributes}
        return encode_to_dict(data)

    def to_dict(self) -> Dict[str, Any]:
        """Output object as a dictionary.

        High-level alternative to :method:`troposphere.BaseAWSObject.dict`.

        """
        return self.dict(by_alias=True, exclude_none=True)

    @classmethod
    def from_dict(
        cls: Type[BaseAWSObjectType], title: str, data: Dict[str, Any]
    ) -> BaseAWSObjectType:
        """Instantiate class from a dict."""
        data.pop("title", None)  # ensure no duplicates
        return cls(title=title, **data)


AWSHelperFnType = TypeVar("AWSHelperFnType", bound="AWSHelperFn")


class AWSHelperFn(mixins.ToJsonMixin):
    """Helper function."""

    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Output object as a dictionary."""
        return encode_to_dict(self.data)

    @staticmethod
    def getdata(data: Union[BaseAWSObject, _T]) -> Union[str, _T]:
        """Get data from object."""
        if isinstance(data, BaseAWSObject):
            return data.title
        return data

    def __eq__(self, other: object) -> bool:
        """Evaluate equality."""
        if isinstance(other, self.__class__):
            return self.data == other.data
        return self.to_dict() == other

    def __hash__(self):
        """Return the object's hash."""
        return hash(self.data)

    def __ne__(self, other: object) -> bool:
        """Evaluate inequality."""
        return not self == other

    def __str__(self) -> str:
        """Return the representation of the object."""
        return json.dumps(self.to_dict())

    @classmethod
    def __get_validators__(
        cls: Type[AWSHelperFnType],
    ) -> Iterator[Callable[[Any], AWSHelperFnType]]:
        """Get validators for custom pydantic field type."""
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        """Modify pydantic JSON schema in place."""

    @classmethod
    def validate(cls: Type[AWSHelperFnType], __v: Any) -> AWSHelperFnType:
        """Validate value."""
        if isinstance(__v, cls):
            return __v
        return cls()


AWSHelperFnOrDict = Union[Dict[str, Any], AWSHelperFn]


class AWSDeclaration(BaseAWSObject):
    """Used for CloudFormation Resource Property objects.

    http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/
    aws-product-property-reference.html

    """

    def ref(self) -> Ref:
        """Return CloudFormation ``Ref`` intrinsic function."""
        return Ref(self)


class Template(BaseModel, mixins.ToJsonMixin):
    """Python representation of a CloudFormation Template."""

    conditions: Dict[str, Any] = Field(default={}, alias="Conditions")
    description: Optional[str] = Field(default=None, alias="Description")
    globals: Optional[AWSHelperFnOrDict] = Field(default=None, alias="Globals")
    mappings: Dict[str, Dict[str, Any]] = Field(default={}, alias="Mappings")
    metadata: Dict[str, Any] = Field(default={}, alias="Metadata")
    outputs: Dict[str, Output] = Field(default={}, alias="Outputs")
    parameters: Dict[str, Parameter] = Field(default={}, alias="Parameters")
    resources: Dict[str, BaseAWSObject] = Field(default={}, alias="Resources")
    rules: Dict[str, Dict[str, Any]] = Field(default={}, alias="Rules")
    transform: Optional[str] = Field(default=None, alias="Transform")
    version: Optional[str] = Field(
        default="2010-09-09", alias="AWSTemplateFormatVersion"
    )

    class Config:
        """Model configuration."""

        allow_population_by_field_name = True
        validate_assignment = True

    @overload
    def _update(
        self, current_value: Dict[str, Any], new_values: BaseAWSObjectType
    ) -> BaseAWSObjectType:
        ...

    @overload
    def _update(
        self,
        current_value: Dict[str, Any],
        new_values: List[BaseAWSObjectType],
    ) -> List[BaseAWSObjectType]:
        ...

    def _update(
        self,
        current_value: Dict[str, Any],
        new_values: Union[List[BaseAWSObjectType], BaseAWSObjectType],
    ) -> Union[List[BaseAWSObjectType], BaseAWSObjectType]:
        """Update attribute vale."""
        if isinstance(new_values, list):
            for v in new_values:
                if v.title in current_value:
                    self.handle_duplicate_key(v.title)
                current_value[v.title] = v
        else:
            if new_values.title in current_value:
                self.handle_duplicate_key(new_values.title)
            current_value[new_values.title] = new_values
        return new_values

    def add_condition(self, name: str, condition: Any) -> str:  # TODO set type
        """Add Template Condition.

        Args:
            name: Name of the condition.
            condition: Condition.

        Returns:
            Name of the condition.

        """
        self.conditions[name] = condition
        return name

    def add_mapping(self, name: str, mapping: Dict[str, Any]) -> None:
        """Add Template Mapping.

        Args:
            name: Name of the mapping.
            mapping: Contents of the mapping.

        """
        if len(self.mappings) >= MAX_MAPPINGS:
            raise ValueError(f"Maximum mappings {MAX_MAPPINGS} reached")
        if name not in self.mappings:
            self.mappings[name] = {}
        self.mappings[name].update(mapping)

    def add_output(self, output: Output) -> Output:
        """Add :class:`troposphere.Output` to Template."""
        if len(self.outputs) >= MAX_OUTPUTS:
            raise ValueError(f"Maximum outputs {MAX_OUTPUTS} reached")
        return self._update(self.outputs, output)

    def add_parameter(self, parameter: Parameter) -> Parameter:
        """Add :class:`troposphere.Parameter` to Template."""
        if len(self.parameters) >= MAX_PARAMETERS:
            raise ValueError(f"Maximum parameters {MAX_PARAMETERS} reached")
        return self._update(self.parameters, parameter)

    def add_parameter_to_group(self, parameter: Union[Parameter, str], group_name: str):
        """Add a parameter under a group (created if needed)."""
        groups: List[ParameterGroupTypedDict] = self.metadata.setdefault(
            "AWS::CloudFormation::Interface", {}
        ).setdefault("ParameterGroups", [])

        if isinstance(parameter, BaseAWSObject):
            parameter = parameter.title

        # Check if group_name already exists
        existing_group: Optional[ParameterGroupTypedDict] = None
        for group in groups:
            if group["Label"]["default"] == group_name:
                existing_group = group
                break

        if existing_group is None:
            existing_group = {
                "Label": {"default": group_name},
                "Parameters": [],
            }
            groups.append(existing_group)

        existing_group["Parameters"].append(parameter)

        return group_name

    def add_resource(self, resource: BaseAWSObjectType) -> BaseAWSObjectType:
        """Add Template Resource."""
        if len(self.resources) >= MAX_RESOURCES:
            raise ValueError(f"Maximum number of resources {MAX_RESOURCES} reached")
        return self._update(self.resources, resource)

    def add_rule(self, name: str, rule: Dict[str, Any]):
        """Add a Rule to the template to enforce extra constraints on the parameters.

        As of June 2019 rules are undocumented in CloudFormation but have the same
        syntax and behavior as in ServiceCatalog:
        https://docs.aws.amazon.com/servicecatalog/latest/adminguide/reference-template_constraint_rules.html

        Args:
            name: Name of the rule.
            rule: a dict with `'Assertions'` (mandatory) and '`RuleCondition'`
                (optional) keys.

        """
        # TODO: check maximum number of Rules, and enforce limit.
        if name in self.rules:
            self.handle_duplicate_key(name)
        self.rules[name] = rule

    def dict(
        self,
        *,
        include: Union[AbstractSetIntStr, MappingIntStrAny] = None,
        exclude: Union[AbstractSetIntStr, MappingIntStrAny] = None,
        by_alias: bool = False,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> Dict[str, Any]:
        """Generate a dictionary representation of the model.

        Wraps method from parent with additional value resolution and formatting
        specific to this usage.

        """
        return encode_to_dict(
            super().dict(
                include=include,
                exclude=exclude,
                by_alias=by_alias,
                skip_defaults=skip_defaults,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
            )
        )

    def get_or_add_parameter(self, parameter: Parameter) -> Parameter:
        """Get a :class:`troposphere.Parameter` from the Template or add it."""
        if parameter.title in self.parameters:
            return self.parameters[parameter.title]
        return self.add_parameter(parameter)

    def handle_duplicate_key(self, key: str) -> NoReturn:
        """Handle duplicate key in template."""
        raise ValueError(f'duplicate key "{key}" detected')

    def set_description(self, description: str) -> None:
        """Set Template description."""
        # this isn't really needed
        self.description = description

    def set_globals(self, value: Union[AWSHelperFn, Dict[str, Any]]) -> None:
        """Set Template globals."""
        # this isn't really needed
        self.globals = value

    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set Template metadata."""
        # this isn't really needed
        self.metadata = metadata

    def set_parameter_label(self, parameter: Union[Parameter, str], label: str) -> None:
        """Set the Label used in the User Interface for the given parameter."""
        labels = self.metadata.setdefault(
            "AWS::CloudFormation::Interface", {}
        ).setdefault("ParameterLabels", {})

        if isinstance(parameter, BaseAWSObject):
            parameter = parameter.title

        labels[parameter] = {"default": label}

    def set_transform(self, transform: str) -> None:
        """Set Template transform."""
        # this isn't really needed
        self.transform = transform

    def set_version(self, version: Optional[str] = None) -> None:
        """Set Template format version."""
        # this isn't really needed if we set the value by default
        if version:
            self.version = version
        else:
            self.version = "2010-09-09"

    def to_dict(self) -> Dict[str, Any]:
        """Output Template as a dictionary."""
        return self.dict(
            by_alias=True,
            exclude={
                i
                for i in [
                    "conditions",
                    "mappings",
                    "metadata",
                    "outputs",
                    "parameters",
                    "resources",
                    "rules",
                ]
                if not getattr(self, i, None)
            },
            exclude_none=True,
        )

    def to_yaml(
        self, clean_up: bool = False, long_form: bool = False, sort_keys: bool = True
    ) -> str:
        """Output Template as JSON."""
        return cfn_flip.to_yaml(
            self.to_json(sort_keys=sort_keys), clean_up=clean_up, long_form=long_form
        )

    @validator("globals")
    def _validate_globals(cls, v: Any, values: Dict[str, Any]) -> Any:
        """Validate value of ``globals`` field."""
        transform = values.get("transform")  # only included for assignment after init
        if transform != SERVERLESS_TRANSFORM:
            raise ValueError(
                "Cannot set Globals for non-Serverless template "
                f"(set transform to '{SERVERLESS_TRANSFORM}' first)"
            )
        return v

    @validator("transform")
    def _validate_transform(cls, v: str, values: Dict[str, Any]) -> str:
        """Validate value of ``transform`` field."""
        if values.get("globals") and v != SERVERLESS_TRANSFORM:
            raise ValueError(
                "Cannot set transform to non-Serverless while using Globals"
            )
        return v

    def __eq__(self, other: object) -> bool:
        """Evaluate equality."""
        if isinstance(other, Template):
            return self.to_json() == other.to_json()
        return False

    def __ne__(self, other: object) -> bool:
        """Evaluate inequality."""
        return not self.__eq__(other)

    def __str__(self) -> str:
        """Return the representation of the object."""
        return self.json()


class Parameter(AWSDeclaration):
    """CloudFormation Parameter."""

    title: str = Field(..., max_length=PARAMETER_TITLE_MAX, regex=r"^[a-zA-Z0-9]+$")
    Type: str  # needs to be set first for other fields to be validated

    AllowedPattern: Optional[str] = None
    AllowedValues: Optional[List[Union[int, float, str]]] = None
    ConstraintDescription: Optional[str] = None
    Default: Optional[Union[int, float, str]] = None
    Description: Optional[str] = None
    MaxLength: Optional[int] = Field(default=None, gt=0)
    MaxValue: Optional[int] = None
    MinLength: Optional[int] = Field(default=None, gt=0)
    MinValue: Optional[int] = None
    NoEcho: Optional[bool] = None

    def add_to_template(self):
        """Add to Template."""
        if self.template is not None:
            self.template.add_parameter(self)

    @validator("Default")
    def _validate_default_type(cls, v: Any, values: Dict[str, Any]) -> Any:
        """Validate type of default value if provided."""

        def _check_type(type_: type, val: object) -> bool:
            try:
                type_(val)
                return True
            except ValueError:
                return False

        param_type = values.get("Type", "")
        error_template = (
            "Parameter default type mismatch: expecting type {0} got {1} with "
            "value {2!r}"
        )
        if param_type == "String" and not isinstance(v, str):
            raise TypeError(error_template.format(param_type, type(v), v))
        if param_type == "Number" and not isinstance(v, (float, int)):
            raise TypeError(error_template.format(param_type, type(v), v))
        if param_type.startswith("List") or param_type == "CommaDelimitedList":
            if not isinstance(v, str):
                raise TypeError(error_template.format(param_type, type(v), v))
            v_split = v.split(",")
            if param_type == "List<Number>":
                for i in v_split:
                    if not _check_type(float, i):
                        raise TypeError(
                            error_template.format(param_type, type(i), v_split)
                        )

    @validator("MaxValue", "MinValue")
    def _validate_number_only_fields(
        cls, v: Any, field: ModelField, values: Dict[str, Any]
    ) -> Any:
        """Validate fields that can only be used with ``Type: Number``."""
        if values.get("Type") != "Number":
            raise ValueError(
                f"{field.name} can only be used with parameters of type String"
            )
        return v

    @validator("AllowedPattern", "MaxLength", "MinLength")
    def _validate_string_only_fields(
        cls, v: Any, field: ModelField, values: Dict[str, Any]
    ) -> Any:
        """Validate fields that can only be used with ``Type: String``."""
        if values.get("Type") != "String":
            raise ValueError(
                f"{field.name} can only be used with parameters of type String"
            )
        return v


class Export(AWSHelperFn):
    """Export value in an ``Output``."""

    def __init__(self, name: str):
        """Instantiate class.

        Args:
            name: Export name.

        """
        self.data = {"Name": name}

    @classmethod
    def validate(cls, v: Any) -> Export:
        """Validate value."""
        if isinstance(v, cls):
            return v
        if isinstance(v, str):
            return cls(v)
        if isinstance(v, dict) and "Name" in v and isinstance(v["Name"], str):
            return cls(v["Name"])
        raise TypeError(f"string or {cls.__qualname__} required")


ExportTypedDict = TypedDict("ExportTypedDict", Name=str)


class Output(AWSDeclaration):
    """Stack output."""

    Description: Optional[str] = None
    Export: Optional[Union[Export, ExportTypedDict]] = None
    Value: Union[str, AWSHelperFnOrDict]

    def add_to_template(self):
        """Add to Template."""
        if self.template is not None:
            self.template.add_output(self)


class AWSAttribute(BaseAWSObject):
    """Used for CloudFormation Resource Attribute objects.

    http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/
    aws-product-attribute-reference.html

    """

    DICT_NAME: ClassVar[Optional[str]] = None


class AWSProperty(BaseAWSObject):
    """Used for CloudFormation Resource Property objects.

    http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/
    aws-product-property-reference.html

    """

    DICT_NAME: ClassVar[Optional[str]] = None


class GenericHelperFn(AWSHelperFn):
    """Used as a fallback for the template generator."""

    def __init__(self, data: Any) -> None:
        """Instantiate class."""
        self.data = self.getdata(data)  # type: ignore


class And(AWSHelperFn):
    """CloudFormation ``Fn::And`` intrinsic function."""

    def __init__(self, *conds: AWSHelperFnOrDict) -> None:
        """Instantiate class."""
        self.data = {"Fn::And": list(conds)}


class Base64(AWSHelperFn):
    """CloudFormation ``Fn::Base64`` intrinsic function."""

    def __init__(self, data: Union[AWSHelperFnOrDict, str, BaseAWSObject]) -> None:
        """Instantiate class."""
        self.data = {"Fn::Base64": data}


class Cidr(AWSHelperFn):
    """CloudFormation ``Fn::Cidr`` intrinsic function."""

    def __init__(
        self, ip_block: str, count: int, cidr_bits: Optional[int] = None
    ) -> None:
        """Instantiate class.

        Args:
            ip_block: The user-specified CIDR address block to be split into
                smaller CIDR blocks.
            count: The number of CIDRs to generate. Valid range is between 1 and 256.
            cidr_bits: The number of subnet bits for the CIDR.
                For example, specifying a value "8" for this parameter will create
                a CIDR with a mask of "/24".

        """
        self.data = {
            "Fn::Cidr": [ip_block, count, cidr_bits] if cidr_bits else [ip_block, count]
        }


class Equals(AWSHelperFn):
    """CloudFormation ``Fn::Equals`` intrinsic function."""

    def __init__(
        self,
        value_one: Union[str, AWSHelperFnOrDict, BaseAWSObject],
        value_two: Union[str, AWSHelperFnOrDict, BaseAWSObject],
    ) -> None:
        """Instantiate class."""
        self.data = {"Fn::Equals": [self.getdata(value_one), self.getdata(value_two)]}


class FindInMap(AWSHelperFn):
    """CloudFormation ``Fn::FindInMap`` intrinsic function."""

    def __init__(
        self,
        map_name: Union[str, AWSHelperFnOrDict],
        top_level_key: Union[str, AWSHelperFnOrDict],
        second_level_key: Union[str, AWSHelperFnOrDict],
    ) -> None:
        """Instantiate class."""
        self.data = {
            "Fn::FindInMap": [self.getdata(map_name), top_level_key, second_level_key]
        }


class GetAtt(AWSHelperFn):
    """CloudFormation ``Fn::GetAtt`` intrinsic function."""

    def __init__(
        self, logical_name: Union[str, AWSHelperFnOrDict, BaseAWSObject], attr_name: str
    ):
        """Instantiate class."""
        self.data = {"Fn::GetAtt": [self.getdata(logical_name), attr_name]}


class GetAZs(AWSHelperFn):
    """CloudFormation ``Fn::GetAZs`` intrinsic function."""

    def __init__(self, region: Union[str, AWSHelperFnOrDict] = "") -> None:
        """Instantiate class."""
        self.data = {"Fn::GetAZs": region}


class If(AWSHelperFn):
    """CloudFormation ``Fn::If`` intrinsic function."""

    def __init__(
        self,
        cond: AWSHelperFnOrDict,
        if_true: Union[BaseAWSObject, AWSHelperFnOrDict],
        if_false: Union[BaseAWSObject, AWSHelperFnOrDict],
    ) -> None:
        """Instantiate class."""
        self.data = {"Fn::If": [self.getdata(cond), if_true, if_false]}


class Join(AWSHelperFn):
    """CloudFormation ``Fn::Join`` intrinsic function."""

    def __init__(self, delimiter: str, values: AWSHelperFnOrDict) -> None:
        """Instantiate class."""
        validators.validate_delimiter(delimiter)
        self.data = {"Fn::Join": [delimiter, values]}


class Not(AWSHelperFn):
    """CloudFormation ``Fn::Not`` intrinsic function."""

    def __init__(self, cond: AWSHelperFnOrDict) -> None:
        """Instantiate class."""
        self.data = {"Fn::Not": [self.getdata(cond)]}


class Or(AWSHelperFn):
    """CloudFormation ``Fn::Or`` intrinsic function."""

    def __init__(self, *conds: AWSHelperFnOrDict) -> None:
        """Instantiate class."""
        self.data = {"Fn::Or": list(conds)}


class Ref(AWSHelperFn):
    """CloudFormation ``Ref`` intrinsic function."""

    def __init__(self, data: Union[BaseAWSObject, str]) -> None:
        """Instantiate class."""
        self.data = {"Ref": self.getdata(data)}

    @classmethod
    def validate(cls, v: Any) -> Ref:
        """Validate value."""
        if isinstance(v, cls):
            return v
        if isinstance(v, str):
            return cls(v)
        if isinstance(v, dict) and "Ref" in v and isinstance(v["Ref"], str):
            return cls(v["Ref"])
        raise TypeError(f"string or {cls.__qualname__} required")


class Select(AWSHelperFn):
    """CloudFormation ``Fn::Select`` intrinsic function."""

    def __init__(
        self, index: int, objects: Union[AWSHelperFn, Dict[str, Any], List[Any]]
    ):
        """Instantiate class."""
        self.data = {"Fn::Select": [index, objects]}


class Split(AWSHelperFn):
    """CloudFormation ``Fn::Split`` intrinsic function."""

    def __init__(self, delimiter: str, values: Union[str, AWSHelperFnOrDict]) -> None:
        """Instantiate class."""
        validators.validate_delimiter(delimiter)
        self.data = {"Fn::Split": [delimiter, values]}


class Sub(AWSHelperFn):
    """CloudFormation ``Fn::Sub`` intrinsic function."""

    def __init__(
        self,
        input_str: str,
        dict_values: Optional[Dict[str, Any]] = None,
        **values: Any,
    ) -> None:
        """Instantiate class."""
        # merge dict
        if dict_values:
            values.update(dict_values)
        self.data = {"Fn::Sub": [input_str, values] if values else input_str}


class DefaultTypedDict(TypedDict):
    """TypedDict that only contains a ``default`` field."""

    default: str


class ParameterGroupTypedDict(TypedDict):
    """``AWS::CloudFormation::Interface.ParameterGroup``."""

    Label: DefaultTypedDict
    Parameters: List[str]


# Pseudo Parameter Ref's
AccountId = Ref(AWS_ACCOUNT_ID)  # pylint: disable=invalid-name
NotificationARNs = Ref(AWS_NOTIFICATION_ARNS)  # pylint: disable=invalid-name
NoValue = Ref(AWS_NO_VALUE)  # pylint: disable=invalid-name
Partition = Ref(AWS_PARTITION)  # pylint: disable=invalid-name
Region = Ref(AWS_REGION)  # pylint: disable=invalid-name
StackId = Ref(AWS_STACK_ID)  # pylint: disable=invalid-name
StackName = Ref(AWS_STACK_NAME)  # pylint: disable=invalid-name
URLSuffix = Ref(AWS_URL_SUFFIX)  # pylint: disable=invalid-name


class AWSObject(BaseAWSObject):
    """AWS Object."""

    DICT_NAME: ClassVar[str] = "Properties"
    RESOURCE_TYPE: ClassVar[str]

    def get_att(self, value: str) -> GetAtt:
        """Return a reference to an attribute of this object."""
        return GetAtt(self, value)

    def dict(
        self,
        *,
        include: Union[AbstractSetIntStr, MappingIntStrAny] = None,
        exclude: Union[AbstractSetIntStr, MappingIntStrAny] = None,
        by_alias: bool = False,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> Dict[str, Any]:
        """Generate a dictionary representation of the model."""
        data = super().dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
        data["Type"] = self.RESOURCE_TYPE
        return data

    def ref(self) -> Ref:
        """Return a reference to this object."""
        return Ref(self)
