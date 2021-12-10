"""Example usage."""
# pylint: disable=invalid-name
from __future__ import annotations

from troposphere import Export, Output, Parameter, Ref, Template, cloudformation

template = Template(Description="Test template.")

test_param = Parameter(
    title="TestParameter",  # title is not requires as a kwarg not a positional arg
    template=template,  # added to the template by passing it here
    Type="String",
    Description="Parameter for testing.",
    Default="foobar",
)

template.add_output(
    Output(
        title="TestOutput0",
        Value=Ref("TestParameter"),  # Ref can use a string
        Export={"Name": "something0"},  # Export can be a dict
        Description="Test output",
    )
)
template.add_output(
    Output(
        title="TestOutput1",
        Value=Ref(test_param),  # Ref can use an object
        Export=Export("something1"),  # Export can be an object
        Description="Test output",
    )
)
template.add_output(
    Output(
        title="TestOutput2",
        Value=test_param.ref(),  # Ref from method
        Export=Export("something1"),  # Export can be an object
        Description="Test output",
    )
)

wc_handle = template.add_resource(
    cloudformation.WaitConditionHandle(title="WaitConditionHandle")
)
template.add_resource(
    cloudformation.WaitCondition(
        title="WaitCondition", Handle=wc_handle.ref(), Timeout=30
    )
)

if __name__ == "__main__":
    print(template.to_json())  # noqa
