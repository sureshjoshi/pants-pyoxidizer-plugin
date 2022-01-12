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
    PackageFieldSet,
)
from pants.engine.fs import CreateDigest, Digest, FileContent
from pants.engine.rules import Get, collect_rules, rule
from pants.engine.process import ProcessResult
from pants.engine.target import Dependencies, DependenciesRequest, Targets
from pants.engine.unions import UnionRule
from pants.util.logging import LogLevel

from experimental.pyoxidizer.target_types import PyOxidizerTarget

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PyOxidizerFieldSet(PackageFieldSet):
    required_fields = (Dependencies,)
    dependencies: Dependencies


@rule(level=LogLevel.DEBUG)
async def package_pyoxidizer_binary(field_set: PyOxidizerFieldSet) -> BuiltPackage:
    targets = await Get(Targets, DependenciesRequest(field_set.dependencies))
    logger.info(
        f"User specified these targets: {[target.address.spec for target in targets]}"
    )

    if len(targets) == 0:
        return None
    target = targets[0]
    wheel = await Get(
        BuiltPackage,
        PackageFieldSet, 
        PyOxidizerFieldSet.create(target)
    )

    logger.info(wheel)

    # Pip install pyoxidizer
    pyoxidizer_pex_get = await Get(
        Pex,
        PexRequest(
            output_filename="pyoxidizer.pex",
            internal_only=True,
            requirements=PexRequirements(["pyoxidizer"]),
            interpreter_constraints=InterpreterConstraints([">=3.9"]),
            main=ConsoleScript("pyoxidizer"),
        ),
    )

    # Create a PyOxidizer configuration file
    contents = dedent(
        """
    def make_exe():
        print('Printing from make_exe inside of pyoxidizer.bzl')
        dist = default_python_distribution()
        policy = dist.make_python_packaging_policy()
        python_config = dist.make_python_interpreter_config()
        exe = dist.to_python_executable(
            name="test-pyox-plugin",
            packaging_policy=policy,
            config=python_config,
        )
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

    output_filename = "test-pyox-plugin"
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
    return BuiltPackage(
        result.output_digest, artifacts=(BuiltPackageArtifact(output_filename),)
    )


def rules():
    return [*collect_rules(), UnionRule(PackageFieldSet, PyOxidizerFieldSet)]
