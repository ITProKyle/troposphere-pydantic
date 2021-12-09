"""Quick and dirty script to patch pydantic for vscode intellisense.

This patch is only needed until the feature is published in a new version of pydantic
(https://github.com/samuelcolvin/pydantic/pull/2721).

Based off these instructions provided by pyright:
https://github.com/microsoft/pyright/blob/main/specs/dataclass_transforms.md#applying-to-pydantic

Usage:
    Download and execute from a Python environment where pydantic is installed.

NOTE: This is has been tested with pydantic==1.8.2. Use at your own risk.

"""  # noqa
import os
import sys
from pathlib import Path

from pkg_resources import get_distribution

indexing_marker = f"class ModelMetaclass(ABCMeta):{os.linesep}"
patch = [
    f"def __dataclass_transform__({os.linesep}",
    f"    *,{os.linesep}",
    f"    eq_default: bool = True,{os.linesep}",
    f"    order_default: bool = False,{os.linesep}",
    f"    kw_only_default: bool = False,{os.linesep}",
    f"    field_descriptors: Tuple[Union[type, Callable[..., Any]], ...] = (()),{os.linesep}",  # noqa
    f") -> Callable[[_T], _T]:{os.linesep}",
    f"    return lambda a:{os.linesep}",
    os.linesep,
    os.linesep,
    f"@__dataclass_transform__(kw_only_default=True, field_descriptors=(Field, FieldInfo)){os.linesep}",  # noqa
]

pydantic_package = get_distribution("pydantic")  # package used in current env
pydantic_path = Path(pydantic_package.location) / "pydantic"

with open(pydantic_path / "main.py", "r+", encoding="utf-8") as f:
    file_contents = f.readlines()

try:
    model_metaclass_index = file_contents.index(indexing_marker)
except ValueError as exc:
    if "not in list" in str(exc):
        print(f"file did not contain the expected line: {indexing_marker}")  # noqa
        print("unable to patch pydantic")  # noqa
        sys.exit(1)
    raise

if file_contents[model_metaclass_index - 1] == patch[-1]:
    print("patch has already been applied")  # noqa
    sys.exit(0)

patched_file_contents = [
    *file_contents[:model_metaclass_index],
    *patch,
    *file_contents[model_metaclass_index:],
]

with open(pydantic_path / "main.py", "w+", encoding="utf-8") as f:
    f.writelines(patched_file_contents)
print("patch applied")  # noqa
