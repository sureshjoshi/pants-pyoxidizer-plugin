from pants.engine.target import Target, COMMON_TARGET_FIELDS

class PyOxidizerTarget(Target):
    alias = "oxy_clean"
    core_fields = (*COMMON_TARGET_FIELDS,)
    help = "The `oxy_clean` target describes how to build a single file executable."
