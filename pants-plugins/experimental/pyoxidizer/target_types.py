from pants.core.goals.package import OutputPathField
from pants.engine.target import Dependencies, Target, COMMON_TARGET_FIELDS


class PyOxidizerDependenciesField(Dependencies):
    supports_transitive_excludes = True


class PyOxidizerTarget(Target):
    alias = "oxy_clean"
    core_fields = (
        *COMMON_TARGET_FIELDS,
        Dependencies,
        OutputPathField,
    )
    help = "The `oxy_clean` target describes how to build a single file executable."
