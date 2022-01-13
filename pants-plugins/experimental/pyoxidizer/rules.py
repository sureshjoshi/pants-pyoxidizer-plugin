from dataclasses import dataclass
import logging
from textwrap import indent, dedent

from pants.backend.python.target_types import ConsoleScript
from pants.backend.python.util_rules.interpreter_constraints import (
    InterpreterConstraints,
)
from pants.backend.python.util_rules.pex import (
    Pex,
    PexProcess,
    PexRequest,
    PexRequirements,
)
from pants.core.goals.package import (
    BuiltPackage,
    BuiltPackageArtifact,
    PackageFieldSet,
)
from pants.engine.fs import CreateDigest, Digest, FileContent, MergeDigests, Snapshot
from pants.engine.rules import Get, MultiGet, collect_rules, rule
from pants.engine.process import ProcessResult
from pants.engine.target import (
    DependenciesRequest,
    FieldSetsPerTarget,
    FieldSetsPerTargetRequest,
    Targets,
)
from pants.engine.unions import UnionRule
from pants.util.logging import LogLevel

from experimental.pyoxidizer.target_types import PyOxidizerEntryPointField, PyOxidizerDependenciesField, PyOxidizerUnclassifiedResources

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PyOxidizerFieldSet(PackageFieldSet):
    required_fields = (PyOxidizerDependenciesField,)
    
    entry_point: PyOxidizerEntryPointField
    dependencies: PyOxidizerDependenciesField
    unclassified_resources: PyOxidizerUnclassifiedResources
    # output_path: OutputPathField # TODO: Remove until API is planned


@rule(level=LogLevel.DEBUG)
async def package_pyoxidizer_binary(field_set: PyOxidizerFieldSet) -> BuiltPackage:
    logger.info(f"Incoming package_pyoxidizer_binary field set: {field_set}")
    targets = await Get(Targets, DependenciesRequest(field_set.dependencies))
    target = targets[0]

    logger.info(
        f"Received these targets inside pyox targets: {target.address.target_name}"
    )

    packages = await Get(
        FieldSetsPerTarget,
        FieldSetsPerTargetRequest(PackageFieldSet, [target]),
    )
    logger.info(f"Retrieved the following FieldSetsPerTarget {packages}")

    built_packages = await MultiGet(
        Get(BuiltPackage, PackageFieldSet, field_set)
        for field_set in packages.field_sets
    )

    # TODO: Can this be walrus'd? Double for with repeated artifact.relpath is ugly
    wheel_relpaths = [
        artifact.relpath for wheel in built_packages for artifact in wheel.artifacts if artifact.relpath is not None
    ]
    logger.info(f"This is the built package retrieved {built_packages}")

    # Pip install pyoxidizer
    pyoxidizer_pex_get = await Get(
        Pex,
        PexRequest(
            output_filename="pyoxidizer.pex",
            internal_only=True,
            requirements=PexRequirements(["pyoxidizer==0.18.0"]),
            interpreter_constraints=InterpreterConstraints([">=3.9"]),
            main=ConsoleScript("pyoxidizer"),
        ),
    )
    
    config_contents = generate_pyoxidizer_config(output_filename=field_set.address.target_name, field_set=field_set, wheel_relpaths=wheel_relpaths)
    config = await Get(
        Digest,
        CreateDigest([FileContent("pyoxidizer.bzl", config_contents.encode("utf-8"))]),
    )
    logger.info(config_contents)

    # Pulling this merged digests idea from the Docker plugin
    digests = [built_package.digest for built_package in built_packages]
    all_digests = (config, *digests)
    merged_digest = await Get(Digest, MergeDigests(d for d in all_digests if d))

    result = await Get(
        ProcessResult,
        PexProcess(
            pyoxidizer_pex_get,
            argv=["build"],
            description="Running PyOxidizer build (...this can take a minute...)",
            input_digest=merged_digest,
            level=LogLevel.DEBUG,
            output_directories=["build"],
        ),
    )
    # logger.info(result.output_digest)
    snapshot = await Get(Snapshot, Digest, result.output_digest)
    artifacts = [BuiltPackageArtifact(file) for file in snapshot.files]
    return BuiltPackage(
        result.output_digest,
        artifacts=tuple(artifacts),
    )


def rules():
    return [*collect_rules(), UnionRule(PackageFieldSet, PyOxidizerFieldSet)]


# TODO: Can this be converted into a jinja template or similar sitting in the repo?
def generate_pyoxidizer_config(output_filename: str, field_set: PyOxidizerFieldSet, wheel_relpaths: list[str]) -> str:
    
    # Conditionally add a config line for the entry point (defaults to REPL)
    entry_point = field_set.entry_point.value
    run_module_config = f"python_config.run_module = '{entry_point}'" if entry_point is not None else ""

    
    # field_set.unclassified_resources.value
    # Add resources that need a specific location
    unclassified_resources = field_set.unclassified_resources.value
    download_to_fs_config = ""
    if unclassified_resources is not None:
        download_to_fs_config = dedent(
            f"""
            for resource in exe.pip_download({list(unclassified_resources)}):
                resource.add_location = "filesystem-relative:lib"
                exe.add_python_resource(resource)"""
        )
        # TODO: Okay, this is just getting ridiculous - definitely need a proper template
        download_to_fs_config = indent(download_to_fs_config, "        ")


    contents = f"""
    def make_exe():
        dist = default_python_distribution()
        policy = dist.make_python_packaging_policy()

        # Note: Adding this for pydanic and libs that have the "unable to load from memory" error
        # https://github.com/indygreg/PyOxidizer/issues/438
        policy.resources_location_fallback = "filesystem-relative:lib"
        
        python_config = dist.make_python_interpreter_config()
        {run_module_config}
        
        exe = dist.to_python_executable(
            name="{output_filename}",
            packaging_policy=policy,
            config=python_config,
        )

        exe.add_python_resources(exe.pip_download({wheel_relpaths}))
        {download_to_fs_config}

        return exe

    def make_embedded_resources(exe):
        return exe.to_embedded_resources()

    def make_install(exe):
        # Create an object that represents our installed application file layout.
        files = FileManifest()
        # Add the generated executable to our install layout in the root directory.
        files.add_python_resource(".", exe)
        return files

    register_target("exe", make_exe)
    register_target("resources", make_embedded_resources, depends=["exe"], default_build_script=True)
    register_target("install", make_install, depends=["exe"], default=True)
    resolve_targets()
        """

    logger.info(contents)
    return dedent(contents)