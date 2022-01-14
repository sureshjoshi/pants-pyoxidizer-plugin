from pants.backend.python.target_types import PexEntryPointField
from pants.core.goals.package import OutputPathField
from pants.engine.target import (
    Dependencies,
    Field,
    SingleSourceField,
    StringField,
    StringSequenceField,
    Target,
    COMMON_TARGET_FIELDS,
)

# TODO: This runs into https://github.com/pantsbuild/pants/issues/13587
# class PyOxidizerEntryPointField(PexEntryPointField):
#     pass


class PyOxidizerEntryPointField(StringField):
    alias = "entry_point"
    default = None
    help = "TODO1"


class PyOxidizerDependenciesField(Dependencies):
    pass


class PyOxidizerUnclassifiedResources(StringSequenceField):
    alias = "filesystem_resources"
    help = """Adds support for listing dependencies that MUST be installed to the filesystem (e.g. Numpy)
        https://pyoxidizer.readthedocs.io/en/stable/pyoxidizer_packaging_additional_files.html#installing-unclassified-files-on-the-filesystem"""


# TODO: I think this should be automatically picked up, like isort or black configs - just not sure how to access the source root from the oxy_clean target
class PyOxidizerConfigSourceField(SingleSourceField):
    alias = "config"
    default = None
    required = False
    expected_file_extensions = (".bzl",)


# TODO: Output Path is useless right now, since PyOx builds elsewhere
class PyOxidizerTarget(Target):
    alias = "oxy_clean"
    core_fields = (
        *COMMON_TARGET_FIELDS,
        PyOxidizerConfigSourceField,
        PyOxidizerDependenciesField,
        PyOxidizerEntryPointField,
        PyOxidizerUnclassifiedResources,
        # OutputPathField, # TODO: Remove until API is planned
    )
    help = "The `oxy_clean` target describes how to build a single file executable."
