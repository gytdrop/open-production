"""PipelineRunner - walks Stages 2 -> 22 using ProductionService as the source of truth."""
from __future__ import annotations
import sys
from pathlib import Path

# Make ``src/`` importable so internal `from agents.X` style imports inside
# the agents / audit / validation / tools subpackages resolve when this
# runner is invoked as ``python -m src.cli.run`` (where only the project
# root, not ``src/`` itself, is on ``sys.path``). Without this bootstrap
# the agents package is unreachable even though ``src.agents`` is.
_THIS_DIR = Path(__file__).resolve().parent
_SRC_ROOT = _THIS_DIR.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from src.agents.confirm_gate import ConfirmSink  # noqa: E402
from src.demo_flow import PauseForHuman, run_pipeline  # noqa: E402
from src.schema.production_document import IntentDocument, Production  # noqa: E402

__all__ = ["PipelineRunner", "PauseForHuman"]


class PipelineRunner:
    def __init__(self, sink=None, llm_client=None):
        self.sink = sink
        self.llm_client = llm_client

    def run(self, intent, out_dir):
        intent_dict = {
            "topic": intent.topic,
            "audience": intent.audience,
            "tone": intent.tone,
            "platform": intent.platform,
        }
        return run_pipeline(
            intent_dict,
            out_dir,
            sink=self.sink,
            llm_client=self.llm_client,
        )
