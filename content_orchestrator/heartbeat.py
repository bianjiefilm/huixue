"""
Heartbeat logging for pipeline steps.
Records step timing for generate / fix / import commands.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("pipeline.heartbeat")


class HeartbeatLogger:
    """Logs pipeline commands with timing."""

    def __init__(self, stage_id: int, log_dir: str = "content_orchestrator/logs"):
        self.stage_id = stage_id
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.events: list[dict[str, Any]] = []
        self._start_time = datetime.utcnow()
        self.log_file = self.log_dir / f"stage_{stage_id}_{self._start_time.strftime('%Y%m%d_%H%M%S')}.jsonl"

    def log(
        self,
        step: str,
        status: str,
        duration_seconds: Optional[float] = None,
        metrics: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "stage_id": self.stage_id,
            "step": step,
            "status": status,
            "duration_seconds": duration_seconds,
            "metrics": metrics or {},
            "error": error,
        }
        self.events.append(event)
        with open(self.log_file, "a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

        msg = f"[{step}] {status}"
        if duration_seconds:
            msg += f" ({duration_seconds:.1f}s)"
        if error:
            msg += f" ERROR: {error}"
        logger.info(msg)

    def log_start(self, step: str) -> datetime:
        self.log(step, "started")
        return datetime.utcnow()

    def log_done(
        self,
        step: str,
        start_time: datetime,
        metrics: Optional[dict[str, Any]] = None,
    ) -> float:
        duration = (datetime.utcnow() - start_time).total_seconds()
        self.log(step, "done", duration_seconds=duration, metrics=metrics)
        return duration

    def log_error(self, step: str, start_time: datetime, error: str) -> float:
        duration = (datetime.utcnow() - start_time).total_seconds()
        self.log(step, "error", duration_seconds=duration, error=error)
        return duration

    def get_summary(self) -> dict[str, Any]:
        total_duration = (datetime.utcnow() - self._start_time).total_seconds()
        steps = {}
        for event in self.events:
            step = event["step"]
            if step not in steps:
                steps[step] = {"started": 0, "done": 0, "errors": 0}
            if event["status"] == "started":
                steps[step]["started"] += 1
            elif event["status"] == "done":
                steps[step]["done"] += 1
            elif event["status"] == "error":
                steps[step]["errors"] += 1

        return {
            "stage_id": self.stage_id,
            "total_duration_seconds": round(total_duration, 1),
            "steps": steps,
            "total_events": len(self.events),
            "log_file": str(self.log_file),
        }

    def print_summary(self) -> None:
        summary = self.get_summary()
        print("\n" + "=" * 50)
        print(f"Stage {self.stage_id} Summary")
        print("=" * 50)
        print(f"Total duration: {summary['total_duration_seconds']:.1f}s")
        print(f"Total events: {summary['total_events']}")
        print("\nSteps:")
        for step, counts in summary["steps"].items():
            errors = f" ({counts['errors']} errors)" if counts["errors"] > 0 else ""
            print(f"  {step}: {counts['done']}/{counts['started']} done{errors}")
        print("=" * 50)
