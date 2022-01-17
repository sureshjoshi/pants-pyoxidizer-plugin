from textwrap import dedent

from experimental.pyoxidizer.subsystem import PyOxidizer, rules as subsystem_rules
from experimental.pyoxidizer.rules import rules as pyoxidizer_rules, PyOxidizerFieldSet
from experimental.pyoxidizer.target_types import PyOxidizerTarget

from pants.backend.python.macros.python_artifact import PythonArtifact
from pants.backend.python.target_types import (
    PythonDistribution,
    PythonSourcesGeneratorTarget,
)
from pants.backend.python.util_rules import pex_from_targets
from pants.core.goals.package import BuiltPackage
from pants.engine.addresses import Address
from pants.testutil.rule_runner import QueryRule, RuleRunner

import pytest


@pytest.fixture
def rule_runner() -> RuleRunner:
    return RuleRunner(
        rules=[
            *pyoxidizer_rules(),
            *subsystem_rules(),
            *pex_from_targets.rules(),
            QueryRule(BuiltPackage, [PyOxidizer, PyOxidizerFieldSet]),
        ],
        target_types=[
            PythonSourcesGeneratorTarget,
            PythonDistribution,
            PyOxidizerTarget,
        ],
        objects={"python_artifact": PythonArtifact},
    )


def project_files() -> dict[str, str]:
    return {
        "src/BUILD": dedent(
            f"""\
            python_sources(
                name="libtest"
            )
            python_distribution(
                name="test-dist",
                dependencies=[":libtest"],
                wheel=True,
                sdist=False,
                provides=python_artifact(
                    name="my-package",
                    version="0.1.0",
              ),
            )
            pyoxidizer_binary(
                name="test-bin",
                entry_point="helloworld.main",
                dependencies=[":test-dist"],
            )
            """
        ),
        "src/main.py": """print("hello test")""",
    }


def test_something(rule_runner: RuleRunner):
    rule_runner.write_files(project_files())
    tgt = rule_runner.get_target(Address("src", target_name="test-bin"))

    field_set = PyOxidizerFieldSet.create(tgt)
    result = rule_runner.request(BuiltPackage, [field_set])
    print(result)
