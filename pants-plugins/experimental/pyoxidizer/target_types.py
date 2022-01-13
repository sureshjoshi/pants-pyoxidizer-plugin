from pants.backend.python.target_types import PexEntryPointField
from pants.core.goals.package import OutputPathField
from pants.engine.target import Dependencies, Target, COMMON_TARGET_FIELDS

class PyOxidizerEntryPointField(PexEntryPointField):
    pass

class PyOxidizerDependenciesField(Dependencies):
    pass


# TODO: Output Path is useless right now, since PyOx builds elsewhere
class PyOxidizerTarget(Target):
    alias = "oxy_clean"
    core_fields = (
        *COMMON_TARGET_FIELDS,
        PyOxidizerEntryPointField,
        PyOxidizerDependenciesField,
        OutputPathField,
    )
    help = "The `oxy_clean` target describes how to build a single file executable."
