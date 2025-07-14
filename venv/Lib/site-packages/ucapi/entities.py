"""
Entity store.

:copyright: (c) 2023 by Unfolded Circle ApS.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from asyncio import AbstractEventLoop
from typing import Any, Callable

from pyee.asyncio import AsyncIOEventEmitter

from ucapi.api_definitions import Events
from ucapi.entity import Entity

_LOG = logging.getLogger(__name__)
_LOG.setLevel(logging.DEBUG)


class Entities:
    """Simple entity storage."""

    def __init__(self, identifier: str, loop: AbstractEventLoop):
        """
        Create entity storage instance with the given identifier.

        :param identifier: storage identifier.
        :param loop: event loop
        """
        self._id: str = identifier
        self._storage = {}
        self._events = AsyncIOEventEmitter(loop)

    def contains(self, entity_id: str) -> bool:
        """Check if storage contains an entity with given identifier."""
        return entity_id in self._storage

    def get(self, entity_id: str) -> Entity | None:
        """Retrieve entity with given identifier."""
        if entity_id not in self._storage:
            _LOG.debug("[%s]: entity not found: '%s'", self._id, entity_id)
            return None

        return self._storage[entity_id]

    def add(self, entity: Entity) -> bool:
        """Add entity to storage."""
        if entity.id in self._storage:
            _LOG.debug("[%s] entity already exists: '%s'", self._id, entity.id)
            return False

        self._storage[entity.id] = entity
        _LOG.debug("[%s] entity added: '%s'", self._id, entity.id)
        return True

    def remove(self, entity_id: str) -> bool:
        """Remove entity from storage."""
        if entity_id not in self._storage:
            _LOG.debug("[%s] cannot remove entity '%s': not found", self._id, entity_id)
            return True

        del self._storage[entity_id]
        _LOG.debug("[%s] entity deleted: %s", self._id, entity_id)
        return True

    def update_attributes(self, entity_id: str, attributes: dict[str, Any]) -> bool:
        """Update entity attributes."""
        if entity_id not in self._storage:
            _LOG.debug(
                "[%s] cannot update entity attributes '%s': not found",
                self._id,
                entity_id,
            )
            return False

        for key in attributes:
            self._storage[entity_id].attributes[key] = attributes[key]

        self._events.emit(
            Events.ENTITY_ATTRIBUTES_UPDATED,
            entity_id,
            self._storage[entity_id].entity_type,
            attributes,
        )

        _LOG.debug("[%s]: entity '%s' attributes updated", self._id, entity_id)
        return True

    def get_all(self) -> list[dict[str, Any]]:
        """
        Get all entity information in storage.

        Attributes are not returned.
        """
        entities = []

        for entity in self._storage.values():
            res = {
                "entity_id": entity.id,
                "entity_type": entity.entity_type,
                "device_id": entity.device_id,
                "features": entity.features,
                "name": entity.name,
            }
            if entity.device_class:
                res["device_class"] = entity.device_class
            if entity.options:
                res["options"] = entity.options
            if entity.area:
                res["area"] = entity.area

            entities.append(res)

        return entities

    async def get_states(self) -> list[dict[str, Any]]:
        """
        Get all entity state information.

        The returned dict includes: entity_id, entity_type, device_id, attributes.
        """
        entities = []

        for entity in self._storage.values():
            res = {
                "entity_id": entity.id,
                "entity_type": entity.entity_type,
                "device_id": entity.device_id,
                "attributes": entity.attributes,
            }

            entities.append(res)

        return entities

    def clear(self):
        """Remove all entities from storage."""
        self._storage = {}

    def add_listener(self, event: Events, f: Callable) -> None:
        """
        Register a callback handler for the given event.

        :param event: the event
        :param f: callback handler
        """
        self._events.add_listener(event, f)

    def remove_listener(self, event: Events, f: Callable) -> None:
        """
        Remove the callback handler for the given event.

        :param event: the event
        :param f: callback handler
        """
        self._events.remove_listener(event, f)

    def remove_all_listeners(self, event: Events | None) -> None:
        """
        Remove all listeners attached to ``event``.

        If ``event`` is ``None``, remove all listeners on all events.

        :param event: the event
        """
        self._events.remove_all_listeners(event)

    ##############
    # Properties #
    ##############

    @property
    def id(self) -> str:
        """Return storage identifier."""
        return self._id
