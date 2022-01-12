from dataclasses import dataclass, field
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
from pants.engine.fs import CreateDigest, Digest, FileContent
from pants.engine.rules import Get, collect_rules, rule
from pants.engine.process import ProcessResult
from pants.engine.target import Dependencies, DependenciesRequest, FieldSetsPerTarget, FieldSetsPerTargetRequest, Targets
from pants.engine.unions import UnionRule
from pants.util.logging import LogLevel

from experimental.pyoxidizer.target_types import PyOxidizerTarget

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PyOxidizerFieldSet(PackageFieldSet):
    required_fields = (Dependencies,)
    dependencies: Dependencies
    output_path: OutputPathField


@rule(level=LogLevel.DEBUG)
async def package_pyoxidizer_binary(field_set: PyOxidizerFieldSet) -> BuiltPackage:
    logger.info(f"PyOxidizer field set: {field_set}")

    targets = await Get(Targets, DependenciesRequest(field_set.dependencies))

    for target in targets:
        logger.info(
            f"Received these targets inside pyox targets: {target.address.target_name}"
        )
        if "dist" not in target.address.spec:
            continue

        logger.info("Creating Wheel")

        packages = await Get(
            FieldSetsPerTarget,
            FieldSetsPerTargetRequest(PackageFieldSet, [target]),
        )
        logger.info(f"Retrieved the following FieldSetsPerTarget {packages}")

        for package in packages.field_sets:
            built_package = await Get(
                BuiltPackage,
                PackageFieldSet,
                package
            )
            logger.info(f"This is the built package retrieved {built_package}")
            # TODO: Limit for wheels only
            wheel_relpaths = [artifact.relpath for artifact in built_package.artifacts if artifact.relpath]
            logger.info(f"This is the list of compiled wheels: {wheel_relpaths}")

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
        print('Printing from make_exe inside of pyoxidizer.bzl')
        dist = default_python_distribution()
        policy = dist.make_python_packaging_policy()
        python_config = dist.make_python_interpreter_config()
        exe = dist.to_python_executable(
            name="{output_filename}",
            packaging_policy=policy,
            config=python_config,
        )
        exe.add_python_resources(exe.pip_download(['pyflakes']))
        exe.add_python_resources(exe.read_package_root(
            path="./",
            packages=["helloworld_dist-0.0.1-py3-none-any.whl"],
        ))
        return exe
    register_target("exe", make_exe)
    #register_target("resources", make_embedded_resources, depends=["exe"], default_build_script=True)
    #register_target("install", make_install, depends=["exe"], default=True)
    #register_target("msi_installer", make_msi, depends=["exe"])
    resolve_targets()
        """
    )

    config = await Get(
        Digest,
        CreateDigest([FileContent("pyoxidizer.bzl", contents.encode("utf-8"))]),
    )
    logger.debug(config)

    result = await Get(
        ProcessResult,
        PexProcess(
            pyoxidizer_pex_get,
            argv=["build"],
            description="Running PyOxidizer build (...this can take a minute...)",
            input_digest=config,
            level=LogLevel.DEBUG,
            output_files=(output_filename,),
        ),
    )
    
    logger.info("Completed running pyoxidizer, hopefully it ends up somewhere good")
    logger.info(result.stdout)
    
    return BuiltPackage(
        result.output_digest, artifacts=(BuiltPackageArtifact(output_filename),)
    )


def rules():
    return [*collect_rules(), UnionRule(PackageFieldSet, PyOxidizerFieldSet)]
