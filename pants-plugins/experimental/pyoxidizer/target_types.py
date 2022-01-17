from pants.backend.python.target_types import PexEntryPointField
from pants.core.goals.package import OutputPathField
from pants.engine.target import (
    COMMON_TARGET_FIELDS,
    Dependencies,
    Field,
    SingleSourceField,
    StringField,
    StringSequenceField,
    Target,
)

# TODO: This runs into https://github.com/pantsbuild/pants/issues/13587
# class PyOxidizerEntryPointField(PexEntryPointField):
#     pass


class PyOxidizerEntryPointField(StringField):
    alias = "entry_point"
    default = None
    help = "TODO: No validation or error handling of entry_point value."


class PyOxidizerDependenciesField(Dependencies):
    pass


class PyOxidizerUnclassifiedResources(StringSequenceField):
    alias = "filesystem_resources"
    help = """Adds support for listing dependencies that MUST be installed to the filesystem (e.g. Numpy)
        https://pyoxidizer.readthedocs.io/en/stable/pyoxidizer_packaging_additional_files.html#installing-unclassified-files-on-the-filesystem"""


# TODO: I think this should be automatically picked up, like isort or black configs - just not sure how to access the source root from the pyoxidizer_binary target
class PyOxidizerConfigSourceField(SingleSourceField):
    alias = "template"
    default = None
    required = False
    expected_file_extensions = (".bzlt",)
    expected_num_files = range(0, 2)
    help = """Adds support for passing in a custom configuration and only injecting certain parameters from the Pants build process.
    Path is relative to the BUILD file's directory.
    Template requires a .bzlt extension. Parameters must be prefixed by $ or surrounded with ${ }
    Template parameters: 
        - ENTRY_POINT - The entry_point passed to this target (or None)
        - NAME - This target's name
        - WHEELS - All python distributions passed to this target (or [])
    """


# TODO: Output Path is useless right now, since PyOx builds elsewhere
class PyOxidizerTarget(Target):
    alias = "pyoxidizer_binary"
    core_fields = (
        *COMMON_TARGET_FIELDS,
        PyOxidizerConfigSourceField,
        PyOxidizerDependenciesField,
        PyOxidizerEntryPointField,
        PyOxidizerUnclassifiedResources,
        # OutputPathField, # TODO: Remove until API is planned
    )
    help = "The `pyoxidizer_binary` target describes how to build a single file executable."
