from dataclasses import dataclass


@dataclass
class ScheduledTask:
    name: str
    frequency: int
    last_run: int | None = None

    def is_due(self, now: int) -> bool:
        return self.last_run is None or now - self.last_run >= self.frequency

    def mark_run(self, now: int) -> None:
        self.last_run = now


def due_tasks(tasks: list[ScheduledTask], now: int) -> list[ScheduledTask]:
    return [task for task in tasks if task.is_due(now)]
