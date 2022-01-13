from pants.backend.python.target_types import PexEntryPointField
from pants.core.goals.package import OutputPathField
from pants.engine.target import Dependencies, Field, StringField, StringSequenceField, Target, COMMON_TARGET_FIELDS

# TODO: This runs into https://github.com/pantsbuild/pants/issues/13587
# class PyOxidizerEntryPointField(PexEntryPointField):
#     pass

class PyOxidizerEntryPointField(StringField):
    alias = "entry_point"
    default = None
    help = (
        "TODO1"
    )

class PyOxidizerDependenciesField(Dependencies):
    pass

class PyOxidizerUnclassifiedResources(StringSequenceField):
    alias = "filesystem_resources"
    help = """Adds support for listing dependencies that MUST be installed to the filesystem (e.g. Numpy)
        https://pyoxidizer.readthedocs.io/en/stable/pyoxidizer_packaging_additional_files.html#installing-unclassified-files-on-the-filesystem"""
    


# TODO: Output Path is useless right now, since PyOx builds elsewhere
class PyOxidizerTarget(Target):
    alias = "oxy_clean"
    core_fields = (
        *COMMON_TARGET_FIELDS,
        PyOxidizerEntryPointField,
        PyOxidizerDependenciesField,
        PyOxidizerUnclassifiedResources,
        # OutputPathField, # TODO: Remove until API is planned
    )
    help = "The `oxy_clean` target describes how to build a single file executable."
