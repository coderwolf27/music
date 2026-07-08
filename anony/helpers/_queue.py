# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of EarBudBot


from collections import defaultdict, deque
from random import randrange
from typing import Union

from ._dataclass import Media, Track

MediaItem = Union[Media, Track]

HISTORY_LIMIT = 20


class Queue:
    def __init__(self):
        self.queues: dict[int, deque[MediaItem]] = defaultdict(deque)
        self.history: dict[int, deque[MediaItem]] = defaultdict(deque)
        self.shuffle_state: dict[int, bool] = defaultdict(bool)

    def add(self, chat_id: int, item: MediaItem) -> int:
        """Add an item to the queue and return its position (1-based)."""
        self.queues[chat_id].append(item)
        return len(self.queues[chat_id]) - 1

    def check_item(self, chat_id: int, item_id: str) -> tuple[int, MediaItem | None]:
        """Check if an item with the given ID exists in the queue."""
        pos, track = next(
            (
                (i, track)
                for i, track in enumerate(list(self.queues[chat_id]))
                if track.id == item_id
            ),
            (-1, None),
        )
        return pos, track

    def force_add(
        self, chat_id: int, item: MediaItem, remove: int | bool = False
    ) -> None:
        """Replace the currently playing item with a new one."""
        self.remove_current(chat_id)
        self.queues[chat_id].appendleft(item)
        if remove:
            self.queues[chat_id].rotate(-remove)
            self.queues[chat_id].popleft()
            self.queues[chat_id].rotate(remove)

    def get_current(self, chat_id: int) -> MediaItem | None:
        """Return the currently playing item (first in queue), if any."""
        return self.queues[chat_id][0] if self.queues[chat_id] else None

    def get_next(self, chat_id: int, check: bool = False) -> MediaItem | None:
        """Remove current item and return the next one, or None if empty."""
        if not self.queues[chat_id]:
            return None
        if check:
            return self.queues[chat_id][1] if len(self.queues[chat_id]) > 1 else None

        finished = self.queues[chat_id].popleft()
        self._push_history(chat_id, finished)

        if self.shuffle_state[chat_id] and len(self.queues[chat_id]) > 1:
            pick = randrange(1, len(self.queues[chat_id]))
            self.queues[chat_id].rotate(-pick)
            picked = self.queues[chat_id].popleft()
            self.queues[chat_id].rotate(pick)
            self.queues[chat_id].appendleft(picked)

        return self.queues[chat_id][0] if self.queues[chat_id] else None

    def get_queue(self, chat_id: int) -> list[MediaItem]:
        """Return the full queue including the currently playing item."""
        return list(self.queues[chat_id])

    def remove_current(self, chat_id: int) -> None:
        """Remove the currently playing item only (if exists)."""
        if self.queues[chat_id]:
            self.queues[chat_id].popleft()

    def clear(self, chat_id: int) -> None:
        """Clear the entire queue."""
        self.queues[chat_id].clear()

    # HISTORY / PREVIOUS
    def _push_history(self, chat_id: int, item: MediaItem) -> None:
        self.history[chat_id].append(item)
        while len(self.history[chat_id]) > HISTORY_LIMIT:
            self.history[chat_id].popleft()

    def has_previous(self, chat_id: int) -> bool:
        return bool(self.history[chat_id])

    def get_previous(self, chat_id: int) -> MediaItem | None:
        """Pop and return the last played track, or None if there's no history."""
        if not self.history[chat_id]:
            return None
        return self.history[chat_id].pop()

    # SHUFFLE
    def toggle_shuffle(self, chat_id: int) -> bool:
        """Flip shuffle mode for this chat and return the new state."""
        self.shuffle_state[chat_id] = not self.shuffle_state[chat_id]
        return self.shuffle_state[chat_id]

    def is_shuffle(self, chat_id: int) -> bool:
        return self.shuffle_state[chat_id]
