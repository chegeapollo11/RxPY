from asyncio import Future
from typing import Callable, Optional, Union, TypeVar, Any

import rx
from rx.core import Observable, abc
from rx.disposable import (
    CompositeDisposable,
    SerialDisposable,
    SingleAssignmentDisposable,
)
from rx.scheduler import CurrentThreadScheduler

_T = TypeVar("_T")


def on_error_resume_next_(
    *sources: Union[
        Observable[_T], "Future[_T]", Callable[[Optional[Exception]], Observable[_T]]
    ]
) -> Observable[_T]:
    """Continues an observable sequence that is terminated normally or
    by an exception with the next observable sequence.

    Examples:
        >>> res = rx.on_error_resume_next(xs, ys, zs)

    Returns:
        An observable sequence that concatenates the source sequences,
        even if a sequence terminates exceptionally.
    """

    sources_ = iter(sources)

    def subscribe(
        observer: abc.ObserverBase[_T], scheduler: Optional[abc.SchedulerBase] = None
    ):
        scheduler = scheduler or CurrentThreadScheduler.singleton()

        subscription = SerialDisposable()
        cancelable = SerialDisposable()

        def action(scheduler: abc.SchedulerBase, state: Optional[Exception] = None):
            try:
                source = next(sources_)
            except StopIteration:
                observer.on_completed()
                return

            # Allow source to be a factory method taking an error
            source = source(state) if callable(source) else source
            current = rx.from_future(source) if isinstance(source, Future) else source

            d = SingleAssignmentDisposable()
            subscription.disposable = d

            def on_resume(state: Optional[Exception] = None):
                scheduler.schedule(action, state)

            d.disposable = current.subscribe_(
                observer.on_next, on_resume, on_resume, scheduler
            )

        cancelable.disposable = scheduler.schedule(action)
        return CompositeDisposable(subscription, cancelable)

    return Observable(subscribe)


__all__ = ["on_error_resume_next_"]
