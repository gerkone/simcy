"""
Shared resources supporting priorities and preemption.

These resources can be used to limit the number of processes using them
concurrently. A process needs to *request* the usage right to a resource. Once
the usage right is not needed anymore it has to be *released*. A gas station
can be modelled as a resource with a limited amount of fuel-pumps. Vehicles
arrive at the gas station and request to use a fuel-pump. If all fuel-pumps are
in use, the vehicle needs to wait until one of the users has finished refueling
and releases its fuel-pump.

These resources can be used by a limited number of processes at a time.
Processes *request* these resources to become a user and have to *release* them
once they are done. For example, a gas station with a limited number of fuel
pumps can be modeled with a `Resource`. Arriving vehicles request a fuel-pump.
Once one is available they refuel. When they are done, the release the
fuel-pump and leave the gas station.

Requesting a resource is modelled as "putting a process' token into the
resources" and releasing a resources correspondingly as "getting a process'
token out of the resource". Thus, calling ``request()``/``release()`` is
equivalent to calling ``put()``/``get()``. Note, that releasing a resource will
always succeed immediately, no matter if a process is actually using a resource
or not.

Besides :class:`Resource`, there is a :class:`PriorityResource`, where
processes can define a request priority, and a :class:`PreemptiveResource`
whose resource users can be preempted by requests with a higher priority.

"""
import heapq

from dataclasses import dataclass, field
from types import TracebackType
from typing import Any, List, Optional, Type

from simcy.core import Environment, SimTime
from simcy.events import Process
from simcy.resources import base

class Preempted:
    """Cause of an preemption :class:`~simcy.exceptions.Interrupt` containing
    information about the preemption.

    """

    def __init__(
        self,
        by: Optional[Process],
        usage_since: Optional[SimTime],
        resource: 'Resource',
    ):
        self.by = by
        """The preempting :class:`simcy.events.Process`."""
        self.usage_since = usage_since
        """The simulation time at which the preempted process started to use
        the resource."""
        self.resource = resource
        """The resource which was lost, i.e., caused the preemption."""


class Request(base.Put):
    """Request usage of the *resource*. The event is triggered once access is
    granted. Subclass of :class:`simcy.resources.base.Put`.

    If the maximum capacity of users has not yet been reached, the request is
    triggered immediately. If the maximum capacity has been
    reached, the request is triggered once an earlier usage request on the
    resource is released.

    The request is automatically released when the request was created within
    a :keyword:`with` statement.

    """

    resource: 'Resource'

    #: The time at which the request succeeded.
    usage_since: Optional[SimTime] = None

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        super().__exit__(exc_type, exc_value, traceback)
        # Don't release the resource on generator cleanups. This seems to
        # create unclaimable circular references otherwise.
        if exc_type is not GeneratorExit:
            self.resource.release(self)
        return None


class Release(base.Get):
    """Releases the usage of *resource* granted by *request*. This event is
    triggered immediately. Subclass of :class:`simcy.resources.base.Get`.

    """

    def __init__(self, resource: 'Resource', request: Request):
        self.request = request
        """The request (:class:`Request`) that is to be released."""
        super().__init__(resource)


class PriorityRequest(Request):
    """Request the usage of *resource* with a given *priority*. If the
    *resource* supports preemption and *preempt* is ``True`` other usage
    requests of the *resource* may be preempted (see
    :class:`PreemptiveResource` for details).

    This event type inherits :class:`Request` and adds some additional
    attributes needed by :class:`PriorityResource` and
    :class:`PreemptiveResource`

    """

    # cdef public int priority
    # cdef public int preempt
    # cdef public object time
    # cdef public tuple key


    def __init__(
        self, resource: 'Resource', priority: int = 0, preempt: bool = True
    ):
        self.priority = priority
        """The priority of this request. A smaller number means higher
        priority."""

        self.preempt = preempt
        """Indicates whether the request should preempt a resource user or not
        (:class:`PriorityResource` ignores this flag)."""

        self.time = resource._env.now
        """The time at which the request was made."""

        self.key = (self.priority, self.time, not self.preempt)
        """Key for sorting events. Consists of the priority (lower value is
        more important), the time at which the request was made (earlier
        requests are more important) and finally the preemption flag (preempt
        requests are more important)."""

        super().__init__(resource)


cdef class SortedQueue:
    """
    Queue for sorting events by their :attr:`~PriorityRequest.key`
    attribute.
    """

    cdef public list h
    cdef public int counter
    cdef public object maxlen

    def __init__(self, maxlen: Optional[int] = None):
        self.h = []
        self.counter = 0
        self.maxlen = maxlen
        """Maximum length of the queue."""

    def append(self, item: Any) -> None:
        """Sort *item* into the queue.

        Raise a :exc:`RuntimeError` if the queue is full.
        """
        if self.maxlen is not None and len(self.h) >= self.maxlen:
            raise RuntimeError('Cannot append event. Queue is full.')

        self._append(item)

    cdef void _append(self, object item):
        heapq.heappush(self.h, [item.key, self.counter, item])
        self.counter += 1

    def __iter__(self):
        return (p[2] for p in self.h)

    def __getitem__(self, i) -> Any:
        return self.h[i][2]

    def __len__(self) -> int:
        return len(self.h)

    def pop(self, i: int = 0) -> Any:
        return self._pop(i)

    cdef _pop(self, int i):
        if i == 0:
            return heapq.heappop(self.h)[2]
        else:
            self.h[i] = self.h[-1]
            ret = self.h.pop()
            heapq.heapify(self.h)
            return ret[2]

    def remove(self, item) -> Any:
        i = next(i for i in range(len(self.h)) if self.h[i][2] == item)
        return self._pop(i)


class Resource(base.BaseResource):
    """Resource with *capacity* of usage slots that can be requested by
    processes.

    If all slots are taken, requests are enqueued. Once a usage request is
    released, a pending request will be triggered.

    The *env* parameter is the :class:`~simcy.core.Environment` instance the
    resource is bound to.

    """

    # cdef public list users
    # cdef public list queue
    #
    # cdef public object request
    # cdef public object release

    # def __cinit__(self):
    #     self.request = self._request
    #     self.release = self._release

    def __init__(self, env: Environment, capacity: int = 1):
        if capacity <= 0:
            raise ValueError('"capacity" must be > 0.')

        super().__init__(env, capacity)

        self.users: List[Request] = []
        """List of :class:`Request` events for the processes that are currently
        using the resource."""
        self.queue = self.put_queue
        """Queue of pending :class:`Request` events. Alias of
        :attr:`~simcy.resources.base.BaseResource.put_queue`.
        """

    @property
    def count(self) -> int:
        """Number of users currently using the resource."""
        return len(self.users)

    def request(self) -> Request:
        """Request a usage slot."""
        return Request(self)

    def release(self, request: Request) -> Release:
        """Release a usage slot."""
        return Release(self, request)

    def _do_put(self, event: Request) -> None:
        if len(self.users) < self.capacity:
            self.users.append(event)
            event.usage_since = self._env.now
            event.succeed()

    def _do_get(self, event: Release) -> None:
        try:
            self.users.remove(event.request)  # type: ignore
        except ValueError:
            pass
        event.succeed()


class PriorityResource(Resource):
    """A :class:`~simcy.resources.resource.Resource` supporting prioritized
    requests.

    Pending requests in the :attr:`~Resource.queue` are sorted in ascending
    order by their *priority* (that means lower values are more important).

    """

    PutQueue = SortedQueue
    """Type of the put queue. See
    :attr:`~simcy.resources.base.BaseResource.put_queue` for details."""

    GetQueue = list
    """Type of the get queue. See
    :attr:`~simcy.resources.base.BaseResource.get_queue` for details."""

    # def __cinit__(self):
    #     self.request = self._request
    #     self.release = self._release

    def __init__(self, env: Environment, capacity: int = 1):
        super().__init__(env, capacity)

    def request(
            self, priority: int = 0, preempt: bool = True
    ) -> PriorityRequest:
        """Request a usage slot with the given *priority*."""
        return PriorityRequest(self, priority, preempt)

    def release(  # type: ignore[override] # noqa: F821
            self, request: PriorityRequest
    ) -> Release:
        """Release a usage slot."""
        return Release(self, request)

class PreemptiveResource(PriorityResource):
    """A :class:`~simcy.resources.resource.PriorityResource` with preemption.

    If a request is preempted, the process of that request will receive an
    :class:`~simcy.exceptions.Interrupt` with a :class:`Preempted` instance as
    cause.

    """

    def _do_put(  # type: ignore[override] # noqa: F821
        self, event
    ):
        if len(self.users) >= self.capacity and event.preempt:
            # Check if we can preempt another process
            preempt = sorted(self.users, key=lambda e: e.key)[-1]
            if preempt.key > event.key:
                self.users.remove(preempt)
                preempt.proc.interrupt(  # type: ignore
                    Preempted(
                        by=event.proc,
                        usage_since=preempt.usage_since,
                        resource=self,
                    )
                )

        return super()._do_put(event)
