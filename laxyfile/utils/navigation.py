"""
Enhanced Navigation System with Performance Optimizations

This module provides high-performance navigation with debouncing,
throttling, and efficient rendering.
"""

import time
import asyncio
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

from ..utils.logger import Logger


class NavigationMode(Enum):
    """Navigation modes"""
    INSTANT = "instant"       # No delay
    SMOOTH = "smooth"         # Small delay for smooth movement
    BATCHED = "batched"       # Batch multiple movements


@dataclass
class NavigationEvent:
    """Navigation event data"""
    direction: str           # up, down, left, right
    panel: str              # left, right, preview
    timestamp: float
    processed: bool = False


class NavigationThrottle:
    """Ultra-fast navigation throttling system"""

    def __init__(self, delay: float = 0.01):  # 10ms delay for ultra-fast response
        self.delay = delay
        self.last_event_time = 0.0
        self.pending_event: Optional[NavigationEvent] = None
        self.timer_task: Optional[asyncio.Task] = None
        self.logger = Logger("NavigationThrottle")

    def should_process_instantly(self, event: NavigationEvent) -> bool:
        """Check if event should be processed instantly without throttling"""
        current_time = time.time()
        time_since_last = current_time - self.last_event_time

        # For ultra-fast navigation, process most events instantly
        if time_since_last >= self.delay:
            self.last_event_time = current_time
            return True
        return False

    async def process_navigation(self, event: NavigationEvent, callback: Callable):
        """Process navigation event with minimal throttling"""
        current_time = time.time()

        # Cancel previous timer if exists
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()

        # Store the latest event
        self.pending_event = event

        # Check if we need to throttle
        time_since_last = current_time - self.last_event_time

        if time_since_last >= self.delay:
            # Execute immediately for ultra-fast response
            await self._execute_event(callback)
        else:
            # Very minimal delay only when absolutely necessary
            remaining_delay = max(0.005, self.delay - time_since_last)  # Minimum 5ms
            self.timer_task = asyncio.create_task(
                self._delayed_execution(remaining_delay, callback)
            )

    async def _delayed_execution(self, delay: float, callback: Callable):
        """Execute event after delay"""
        try:
            await asyncio.sleep(delay)
            await self._execute_event(callback)
        except asyncio.CancelledError:
            # Timer was cancelled, do nothing
            pass

    async def _execute_event(self, callback: Callable):
        """Execute the pending navigation event"""
        if self.pending_event and not self.pending_event.processed:
            self.last_event_time = time.time()
            self.pending_event.processed = True

            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self.pending_event)
                else:
                    callback(self.pending_event)
            except Exception as e:
                self.logger.error(f"Error executing navigation callback: {e}")

            self.pending_event = None


class FastNavigationManager:
    """Ultra-high-performance navigation manager with instant response"""

    def __init__(self):
        self.logger = Logger("FastNavigationManager")
        self.throttle = NavigationThrottle(delay=0.01)  # 10ms for ultra-fast response
        self.navigation_cache: Dict[str, Any] = {}
        self.last_render_time = 0.0
        self.render_throttle = 0.008  # ~120 FPS for ultra-smooth rendering

        # Performance counters
        self.navigation_count = 0
        self.render_count = 0
        self.cache_hits = 0

    def can_navigate_instantly(self, direction: str, panel: str) -> bool:
        """Check if navigation can be processed instantly"""
        # Always allow instant navigation for better responsiveness
        return True

    async def navigate(self, direction: str, panel: str, callback: Callable):
        """Perform ultra-fast navigation"""
        event = NavigationEvent(
            direction=direction,
            panel=panel,
            timestamp=time.time()
        )

        self.navigation_count += 1

        # Check if we can process instantly
        if self.throttle.should_process_instantly(event):
            # Execute immediately for best performance
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                self.logger.error(f"Error in instant navigation: {e}")
        else:
            # Fallback to throttled processing
            await self.throttle.process_navigation(event, callback)

    def should_render(self) -> bool:
        """Check if we should render based on ultra-fast throttling"""
        current_time = time.time()
        if current_time - self.last_render_time >= self.render_throttle:
            self.last_render_time = current_time
            self.render_count += 1
            return True
        return False

    def cache_navigation_data(self, key: str, data: Any):
        """Cache navigation-related data"""
        self.navigation_cache[key] = {
            'data': data,
            'timestamp': time.time()
        }

    def get_cached_data(self, key: str, max_age: float = 1.0) -> Optional[Any]:
        """Get cached navigation data if still valid"""
        if key in self.navigation_cache:
            cached = self.navigation_cache[key]
            if time.time() - cached['timestamp'] <= max_age:
                self.cache_hits += 1
                return cached['data']
            else:
                # Remove expired cache
                del self.navigation_cache[key]
        return None

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'navigation_count': self.navigation_count,
            'render_count': self.render_count,
            'cache_hits': self.cache_hits,
            'cache_size': len(self.navigation_cache),
            'cache_hit_rate': self.cache_hits / max(1, self.navigation_count)
        }

    def clear_cache(self):
        """Clear navigation cache"""
        self.navigation_cache.clear()
        self.logger.debug("Navigation cache cleared")


class KeyboardDebouncer:
    """Debounces keyboard input to prevent spam"""

    def __init__(self, debounce_time: float = 0.05):
        self.debounce_time = debounce_time
        self.last_key_time: Dict[str, float] = {}
        self.key_timers: Dict[str, asyncio.Task] = {}

    async def process_key(self, key: str, callback: Callable, *args, **kwargs) -> bool:
        """Process key with debouncing"""
        current_time = time.time()

        # Cancel existing timer for this key
        if key in self.key_timers and not self.key_timers[key].done():
            self.key_timers[key].cancel()

        # Check if enough time has passed since last press
        if key in self.last_key_time:
            time_since_last = current_time - self.last_key_time[key]
            if time_since_last < self.debounce_time:
                # Schedule delayed execution
                self.key_timers[key] = asyncio.create_task(
                    self._delayed_key_execution(key, callback, args, kwargs)
                )
                return False

        # Execute immediately
        self.last_key_time[key] = current_time
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
            return True
        except Exception as e:
            print(f"Error in key callback: {e}")
            return False

    async def _delayed_key_execution(self, key: str, callback: Callable, args, kwargs):
        """Execute key callback after debounce delay"""
        try:
            await asyncio.sleep(self.debounce_time)
            self.last_key_time[key] = time.time()

            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except asyncio.CancelledError:
            # Debounce was cancelled, do nothing
            pass
        except Exception as e:
            print(f"Error in delayed key execution: {e}")


# Global instances for performance optimization
navigation_manager = FastNavigationManager()
keyboard_debouncer = KeyboardDebouncer()
