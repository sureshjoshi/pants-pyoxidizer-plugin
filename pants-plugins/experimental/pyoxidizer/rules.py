from dataclasses import dataclass

from pants.engine.rules import Get, collect_rules, rule
from pants.engine.unions import UnionRule
from pants.util.logging import LogLevel
from pants.backend.python.target_types import ConsoleScript
from pants.backend.python.util_rules.interpreter_constraints import InterpreterConstraints
from pants.backend.python.util_rules import pex
from pants.backend.python.util_rules.pex import Pex, PexProcess, PexRequest, PexRequirements, VenvPex, VenvPexProcess
from pants.core.goals.package import (
    BuiltPackage,
    BuiltPackageArtifact,
    OutputPathField,
    PackageFieldSet,
)
from pants.engine.process import FallibleProcessResult, Process, ProcessResult


@dataclass(frozen=True)
class PyOxidizerFieldSet(PackageFieldSet):
    required_fields = ()

@rule(level=LogLevel.DEBUG)
async def package_pyoxidizer_binary() -> BuiltPackage:
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

    output_filename = "myapp"
    result = await Get(
        ProcessResult,
        PexProcess(pyoxidizer_pex_get, argv=["build"], description="Something blah blah", level=LogLevel.DEBUG,output_files=(output_filename,)),
    )
    return BuiltPackage(result.output_digest, artifacts=(BuiltPackageArtifact(output_filename),))
    

def rules():
     return [
        *collect_rules(),
         UnionRule(PackageFieldSet, PyOxidizerFieldSet)
        
        # *pex.rules(),
    ]