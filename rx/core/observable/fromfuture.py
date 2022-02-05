import asyncio
from asyncio import Future
from typing import Any, Optional, TypeVar

from rx.core import Observable, abc
from rx.disposable import Disposable

_T = TypeVar("_T")


def from_future_(future: "Future[_T]") -> Observable[_T]:
    """Converts a Future to an Observable sequence

    Args:
        future -- A Python 3 compatible future.
            https://docs.python.org/3/library/asyncio-task.html#future
            http://www.tornadoweb.org/en/stable/concurrent.html#tornado.concurrent.Future

    Returns:
        An Observable sequence which wraps the existing future success
        and failure.
    """

    def subscribe(
        observer: abc.ObserverBase[Any], scheduler: Optional[abc.SchedulerBase] = None
    ) -> abc.DisposableBase:
        def done(future: "Future[_T]"):
            try:
                value: Any = future.result()
            except (
                Exception,
                asyncio.CancelledError,
            ) as ex:  # pylint: disable=broad-except
                observer.on_error(ex)
            else:
                observer.on_next(value)
                observer.on_completed()

        future.add_done_callback(done)

        def dispose() -> None:
            if future and future.cancel:
                future.cancel()

        return Disposable(dispose)

    return Observable(subscribe)


__all__ = ["from_future_"]
