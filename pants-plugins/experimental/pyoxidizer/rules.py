from dataclasses import dataclass
import logging
from textwrap import dedent

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
    OutputPathField,
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

from experimental.pyoxidizer.target_types import PyOxidizerDependenciesField

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PyOxidizerFieldSet(PackageFieldSet):
    required_fields = (PyOxidizerDependenciesField,)
    dependencies: PyOxidizerDependenciesField
    output_path: OutputPathField


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
    wheel_relpaths = [
        artifact.relpath for wheel in built_packages for artifact in wheel.artifacts
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

    output_filename = field_set.output_path.value_or_default(file_ending=None)
    logger.info(f"PyOxidizer is using this output filename: {output_filename}")

    # Create a PyOxidizer configuration file
    contents = dedent(
        f"""
    def make_exe():
        dist = default_python_distribution()
        policy = dist.make_python_packaging_policy()

        # Note: Adding this for pydanic (unable to load from memory)
        # https://github.com/indygreg/PyOxidizer/issues/438
        policy.resources_location_fallback = "filesystem-relative:lib"
        
        python_config = dist.make_python_interpreter_config()
        #python_config.run_command = "import main; main.say_hello()"
        #python_config.run_module = "main"
        
        exe = dist.to_python_executable(
            name="{output_filename}",
            packaging_policy=policy,
            config=python_config,
        )
        exe.add_python_resources(exe.pip_install({wheel_relpaths}))
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
    )

    config = await Get(
        Digest,
        CreateDigest([FileContent("pyoxidizer.bzl", contents.encode("utf-8"))]),
    )

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
            output_files=(
                f"./build/x86_64-apple-darwin/debug/install/{output_filename}",
            ),
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
