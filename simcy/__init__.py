"""
The ``simcy`` module aggregates simcy's most used components into a single
namespace. This is purely for convenience. You can of course also access
everything (and more!) via their actual submodules.

The following tables list all of the available components in this module.

{toc}

"""
from pkg_resources import get_distribution
from pkgutil import extend_path
from typing import List, Tuple, Type

from simcy.core import Environment
from simcy.rt import RealtimeEnvironment
from simcy.exceptions import simcyException, Interrupt
from simcy.events import Event, Timeout, Process, AllOf, AnyOf
from simcy.resources.resource import (
    Resource, PriorityResource, PreemptiveResource)
from simcy.resources.container import Container
from simcy.resources.store import (
    Store, PriorityItem, PriorityStore, FilterStore)

__all__ = [
    'AllOf',
    'AnyOf',
    'Container',
    'Environment',
    'Event',
    'FilterStore',
    'Interrupt',
    'PreemptiveResource',
    'PriorityItem',
    'PriorityResource',
    'PriorityStore',
    'Process',
    'RealtimeEnvironment',
    'Resource',
    'simcyException',
    'Store',
    'Timeout',
]


def _compile_toc(
    entries: Tuple[Tuple[str, Tuple[Type, ...]], ...],
    section_marker: str = '=',
) -> str:
    """Compiles a list of sections with objects into sphinx formatted
    autosummary directives."""
    toc = ''
    for section, objs in entries:
        toc += '\n\n'
        toc += f'{section}\n'
        toc += f'{section_marker * len(section)}\n\n'
        toc += '.. autosummary::\n\n'
        for obj in objs:
            toc += f'    ~{obj.__module__}.{obj.__name__}\n'
    return toc


_toc = (
    ('Environments', (
        Environment, RealtimeEnvironment,
    )),
    ('Events', (
        Event, Timeout, Process, AllOf, AnyOf, Interrupt,
    )),
    ('Resources', (
        Resource, PriorityResource, PreemptiveResource, Container, Store,
        PriorityItem, PriorityStore, FilterStore,
    )),
    ('Exceptions', (
        simcyException, Interrupt
    )),
)

# Use the _toc to keep the documentation and the implementation in sync.
if __doc__:
    __doc__ = __doc__.format(toc=_compile_toc(_toc))
    assert set(__all__) == {obj.__name__ for _, objs in _toc for obj in objs}

__path__: List[str] = list(extend_path(__path__, __name__))
__version__: str = get_distribution('simcy').version
