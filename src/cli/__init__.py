"""Open Production CLI.

Exposes the ``production`` dispatcher via ``python -m src.cli <subcmd>`` and
also lets each subcommand be invoked directly via ``python -m src.cli.<name>``.

Subcommands:
  timeline  - replay a production's audit trail
  trace     - walk an asset / production lineage DAG
  doctor    - emit a green / yellow / red health report
  compare   - side-by-side diff of two productions
  run       - drive the full 22-stage pipeline from an intent (keystone)
  list      - enumerate every production on disk
"""
from __future__ import annotations

__all__ = ["main"]


def main(argv=None):
    """Delegate to the unified CLI dispatcher."""
    from src.cli.__main__ import main as _main
    return _main(argv)
