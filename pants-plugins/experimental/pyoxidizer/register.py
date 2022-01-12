
from experimental.pyoxidizer.rules import rules as pyoxidizer_rules
from experimental.pyoxidizer.target_types import PyOxidizerTarget


def rules():
    return [*pyoxidizer_rules()]


def target_types():
    return [PyOxidizerTarget]
