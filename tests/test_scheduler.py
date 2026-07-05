from umd_client.scheduler import ScheduledTask, due_tasks


def test_due_tasks_runs_never_run_tasks_and_respects_frequency():
    tasks = [
        ScheduledTask("upload", frequency=30, last_run=None),
        ScheduledTask("display", frequency=300, last_run=100),
        ScheduledTask("camera", frequency=1800, last_run=100),
    ]

    assert [task.name for task in due_tasks(tasks, now=350)] == ["upload"]
    assert [task.name for task in due_tasks(tasks, now=401)] == ["upload", "display"]
