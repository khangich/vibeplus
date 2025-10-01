from __future__ import annotations

from rq import Connection, Queue, Worker

from backend.backend.db import get_redis

listen_queues = ["default"]


def main() -> None:
    redis = get_redis()
    with Connection(redis):
        worker = Worker(list(map(Queue, listen_queues)))
        worker.work()


if __name__ == "__main__":
    main()
