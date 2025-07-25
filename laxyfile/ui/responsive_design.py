"""
Responsive Design and Animation System

This module provides responsive design capabilities and smooth animations
for LaxyFile's user interface, adapting to different terminal sizes.
"""

import asyncio
import time
from typing import Dict, Any, List, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from rich.layout import Layout
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich.columns import Columns

from ..utils.logger import Logger


class BreakPoint(Enum):
    """Screen size breakpoints"""
    MOBILE = "mobile"      # < 60 columns
    TABLET = "tablet"      # 60-100 columns
    DESKTOP = "desktop"    # 100-140 columns
    WIDE = "wide"         # > 140 columns


class AnimationType(Enum):
    """Animation types"""
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    SCALE_IN = "scale_in"
    SCALE_OUT = "scale_out"
    PULSE = "pulse"


@dataclass
class LayoutConfig:
    """Layout configuration for different screen sizes"""
    show_sidebar: bool = True
    show_preview: bool = True
    sidebar_width: int = 20
    preview_width: int = 30
    dual_pane: bool = True
    header_height: int = 3
    footer_height: int = 4
    min_panel_width: int = 30


@dataclass
class AnimationFrame:
    """Single animation frame"""
    content: Any
    duration: float
    easing: str = "linear"


class ResponsiveLayoutManager:
    """Manages responsive layout based on terminal size"""

    def __init__(self, console: Console):
        self.console = console
        self.logger = Logger()

        # Current state
        self.current_width = 0
        self.current_height = 0
        self.current_breakpoint = BreakPoint.DESKTOP

        # Layout configurations for different breakpoints
        self.layout_configs = {
            BreakPoint.MOBILE: LayoutConfig(
                show_sidebar=False,
                show_preview=False,
                dual_pane=False,
                sidebar_width=0,
                preview_width=0,
                header_height=2,
                footer_height=3,
                min_panel_width=20
            ),
            BreakPoint.TABLET: LayoutConfig(
                show_sidebar=False,
                show_preview=True,
                dual_pane=True,
                sidebar_width=0,
                preview_width=25,
                header_height=3,
                footer_height=4,
                min_panel_width=25
            ),
            BreakPoint.DESKTOP: LayoutConfig(
                show_sidebar=True,
                show_preview=True,
                dual_pane=True,
                sidebar_width=20,
                preview_width=30,
                header_height=3,
                footer_height=4,
                min_panel_width=30
            ),
            BreakPoint.WIDE: LayoutConfig(
                show_sidebar=True,
                show_preview=True,
                dual_pane=True,
                sidebar_width=25,
                preview_width=35,
                header_height=3,
                footer_height=4,
                min_panel_width=35
            )
        }

        # Callbacks for layout changes
        self.layout_change_callbacks: List[Callable] = []

    def update_size(self, width: int, height: int) -> bool:
        """Update terminal size and return True if layout should change"""
        old_breakpoint = self.current_breakpoint

        self.current_width = width
        self.current_height = height
        self.current_breakpoint = self._determine_breakpoint(width)

        # Check if breakpoint changed
        if old_breakpoint != self.current_breakpoint:
            self.logger.info(f"Breakpoint changed: {old_breakpoint.value} -> {self.current_breakpoint.value}")
            self._notify_layout_change()
            return True

        return False

    def _determine_breakpoint(self, width: int) -> BreakPoint:
        """Determine breakpoint based on width"""
        if width < 60:
            return BreakPoint.MOBILE
        elif width < 100:
            return BreakPoint.TABLET
        elif width < 140:
            return BreakPoint.DESKTOP
        else:
            return BreakPoint.WIDE

    def get_layout_config(self) -> LayoutConfig:
        """Get current layout configuration"""
        return self.layout_configs[self.current_breakpoint]

    def create_responsive_layout(self) -> La   """Create layout based on current breakpoint"""
        config = self.get_layout_config()
        layout = Layout(name="root")

        # Main structure
        layout.split_column(
            Layout(name="header", size=config.header_height),
            Layout(name="main", ratio=1, minimum_size=10),
            Layout(name="footer", size=config.footer_height)
        )

        # Configure main area based on breakpoint
        if self.current_breakpoint == BreakPoint.MOBILE:
            # Single panel only
            layout["main"] = Layout(name="single_panel")

        elif self.current_breakpoint == BreakPoint.TABLET:
            # Dual pane with preview
            layout["main"].split_row(
                Layout(name="panels", ratio=2, minimum_size=config.min_panel_width),
                Layout(name="preview", size=config.preview_width, minimum_size=20)
            )
            layout["panels"].split_row(
                Layout(name="left_panel", ratio=1),
                Layout(name="right_panel", ratio=1)
            )

        else:  # DESKTOP or WIDE
            # Full layout with sidebar
            main_parts = []

            if config.show_sidebar:
                main_parts.append(Layout(name="sidebar", size=config.sidebar_width, minimum_size=15))

            main_parts.append(Layout(name="panels", ratio=1, minimum_size=config.min_panel_width))

            if config.show_preview:
                main_parts.append(Layout(name="preview", size=config.preview_width, minimum_size=20))

            layout["main"].split_row(*main_parts)

            # Split panels area
            if config.dual_pane:
                layout["panels"].split_row(
                    Layout(name="left_panel", ratio=1),
                    Layout(name="right_panel", ratio=1)
                )

        return layout

    def add_layout_change_callback(self, callback: Callable) -> None:
        """Add callback for layout changes"""
        self.layout_change_callbacks.append(callback)

    def _notify_layout_change(self) -> None:
        """Notify all callbacks of layout change"""
        for callback in self.layout_change_callbacks:
            try:
                callback(self.current_breakpoint, self.get_layout_config())
            except Exception as e:
                self.logger.error(f"Error in layout change callback: {e}")

    def get_optimal_panel_width(self) -> int:
        """Get optimal panel width for current screen size"""
        config = self.get_layout_config()

        available_width = self.current_width
        if config.show_sidebar:
            available_width -= config.sidebar_width
        if config.show_preview:
            available_width -= config.preview_width

        # Account for borders and padding
        available_width -= 6  # Borders and spacing

        if config.dual_pane:
            return max(config.min_panel_width, available_width // 2)
        else:
            return max(config.min_panel_width, available_width)

    def should_show_component(self, component: str) -> bool:
        """Check if component should be shown at current breakpoint"""
        config = self.get_layout_config()

        if component == "sidebar":
            return config.show_sidebar
        elif component == "preview":
            return config.show_preview
        elif component == "dual_pane":
            return config.dual_pane

        return True


class AnimationEngine:
    """Handles smooth animations and transitions"""

    def __init__(self, console: Console):
        self.console = console
        self.logger = Logger()

        # Animation state
        self.active_animations: Dict[str, asyncio.Task] = {}
        self.animation_speed = 1.0  # Speed multiplier

        # Easing functions
        self.easing_functions = {
            "linear": lambda t: t,
            "ease_in": lambda t: t * t,
            "ease_out": lambda t: 1 - (1 - t) * (1 - t),
            "ease_in_out": lambda t: 2 * t * t if t < 0.5 else 1 - 2 * (1 - t) * (1 - t),
            "bounce": lambda t: 1 - abs(1 - 2 * t) if t < 1 else 1
        }

    async def animate_transition(self, animation_id: str, animation_type: AnimationType,
                               duration: float = 0.5, easing: str = "ease_in_out",
                               callback: Optional[Callable] = None) -> None:
        """Animate a transition effect"""
        try:
            # Cancel existing animation with same ID
            if animation_id in self.active_animations:
                self.active_animations[animation_id].cancel()

            # Create and start animation task
            task = asyncio.create_task(
                self._run_animation(animation_type, duration, easing, callback)
            )
            self.active_animations[animation_id] = task

            await task

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error in animation {animation_id}: {e}")
        finally:
            # Clean up
            if animation_id in self.active_animations:
                del self.active_animations[animation_id]

    async def _run_animation(self, animation_type: AnimationType, duration: float,
                           easing: str, callback: Optional[Callable]) -> None:
        """Run the actual animation"""
        start_time = time.time()
        adjusted_duration = duration / self.animation_speed

        easing_func = self.easing_functions.get(easing, self.easing_functions["linear"])

        while True:
            elapsed = time.time() - start_time
            progress = min(elapsed / adjusted_duration, 1.0)

            # Apply easing
            eased_progress = easing_func(progress)

            # Generate animation frame
            frame = self._generate_animation_frame(animation_type, eased_progress)

            # Execute callback if provided
            if callback:
                await callback(frame, eased_progress)

            # Check if animation is complete
            if progress >= 1.0:
                break

            # Wait for next frame (60 FPS)
            await asyncio.sleep(1/60)

    def _generate_animation_frame(self, animation_type: AnimationType,
                                progress: float) -> Dict[str, Any]:
        """Generate animation frame data"""
        frame = {"progress": progress, "type": animation_type.value}

        if animation_type == AnimationType.FADE_IN:
            frame["opacity"] = progress
        elif animation_type == AnimationType.FADE_OUT:
            frame["opacity"] = 1.0 - progress
        elif animation_type == AnimationType.SLIDE_LEFT:
            frame["offset_x"] = -50 * (1.0 - progress)
        elif animation_type == AnimationType.SLIDE_RIGHT:
            frame["offset_x"] = 50 * (1.0 - progress)
        elif animation_type == AnimationType.SLIDE_UP:
            frame["offset_y"] = -10 * (1.0 - progress)
        elif animation_type == AnimationType.SLIDE_DOWN:
            frame["offset_y"] = 10 * (1.0 - progress)
        elif animation_type == AnimationType.SCALE_IN:
            frame["scale"] = progress
        elif animation_type == AnimationType.SCALE_OUT:
            frame["scale"] = 1.0 - progress
        elif animation_type == AnimationType.PULSE:
            frame["scale"] = 1.0 + 0.1 * abs(0.5 - progress) * 2

        return frame

    async def animate_panel_transition(self, old_content: Panel, new_content: Panel,
                                     transition_type: AnimationType = AnimationType.FADE_IN) -> Panel:
        """Animate transition between panel contents"""
        try:
            # Create transition frames
            frames = []
            frame_count = 10

            for i in range(frame_count + 1):
                progress = i / frame_count
                frame = self._generate_animation_frame(transition_type, progress)

                # Create blended content based on animation type
                if transition_type in [AnimationType.FADE_IN, AnimationType.FADE_OUT]:
                    # Simple fade transition
                    if progress < 0.5:
                        frames.append(old_content)
                    else:
                        frames.append(new_content)
                else:
                    # For other animations, just use new content
                    frames.append(new_content)

            # Play animation frames
            for frame in frames:
                # In a real implementation, this would update the display
                await asyncio.sleep(1/30)  # 30 FPS

            return new_content

        except Exception as e:
            self.logger.error(f"Error in panel transition: {e}")
            return new_content

    def set_animation_speed(self, speed: float) -> None:
        """Set global animation speed multiplier"""
        self.animation_speed = max(0.1, min(speed, 5.0))

    def cancel_animation(self, animation_id: str) -> None:
        """Cancel a specific animation"""
        if animation_id in self.active_animations:
            self.active_animations[animation_id].cancel()

    def cancel_all_animations(self) -> None:
        """Cancel all active animations"""
        for task in self.active_animations.values():
            task.cancel()
        self.active_animations.clear()


class ProgressiveRenderer:
    """Handles progressive rendering for large content"""

    def __init__(self, console: Console):
        self.console = console
        self.logger = Logger()

        # Rendering settings
        self.chunk_size = 50  # Items per chunk
        self.render_delay = 0.01  # Delay between chunks

    async def render_large_list(self, items: List[Any], renderer: Callable,
                              progress_callback: Optional[Callable] = None) -> List[Any]:
        """Render large list progressively"""
        try:
            rendered_items = []
            total_items = len(items)

            for i in range(0, total_items, self.chunk_size):
                chunk = items[i:i + self.chunk_size]

                # Render chunk
                chunk_rendered = []
                for item in chunk:
                    try:
                        rendered_item = await renderer(item) if asyncio.iscoroutinefunction(renderer) else renderer(item)
                        chunk_rendered.append(rendered_item)
                    except Exception as e:
                        self.logger.error(f"Error rendering item: {e}")

                rendered_items.extend(chunk_rendered)

                # Update progress
                if progress_callback:
                    progress = (i + len(chunk)) / total_items
                    await progress_callback(progress, f"Rendered {i + len(chunk)}/{total_items} items")

                # Allow other tasks to run
                await asyncio.sleep(self.render_delay)

            return rendered_items

        except Exception as e:
            self.logger.error(f"Error in progressive rendering: {e}")
            return []

    def set_chunk_size(self, size: int) -> None:
        """Set chunk size for progressive rendering"""
        self.chunk_size = max(1, min(size, 1000))

    def set_render_delay(self, delay: float) -> None:
        """Set delay between chunk rendering"""
        self.render_delay = max(0.001, min(delay, 1.0))


class ResponsiveUIManager:
    """Main manager for responsive design and animations"""

    def __init__(self, console: Console):
        self.console = console
        self.logger = Logger()

        # Components
        self.layout_manager = ResponsiveLayoutManager(console)
        self.animation_engine = AnimationEngine(console)
        self.progressive_renderer = ProgressiveRenderer(console)

        # State
        self.current_layout = None
        self.is_animating = False

    async def handle_resize(self, width: int, height: int) -> Optional[Layout]:
        """Handle terminal resize with smooth transitions"""
        try:
            # Check if layout needs to change
            layout_changed = self.layout_manager.update_size(width, height)

            if layout_changed and not self.is_animating:
                self.is_animating = True

                # Create new layout
                new_layout = self.layout_manager.create_responsive_layout()

                # Animate transition if we have an old layout
                if self.current_layout:
                    await self.animation_engine.animate_transition(
                        "layout_change",
                        AnimationType.FADE_IN,
                        duration=0.3,
                        easing="ease_in_out"
                    )

                self.current_layout = new_layout
                self.is_animating = False

                return new_layout

            return None

        except Exception as e:
            self.logger.error(f"Error handling resize: {e}")
            self.is_animating = False
            return None

    def get_current_layout(self) -> Optional[Layout]:
        """Get current responsive layout"""
        if not self.current_layout:
            self.current_layout = self.layout_manager.create_responsive_layout()
        return self.current_layout

    def get_breakpoint_info(self) -> Dict[str, Any]:
        """Get current breakpoint information"""
        return {
            "breakpoint": self.layout_manager.current_breakpoint.value,
            "width": self.layout_manager.current_width,
            "height": self.layout_manager.current_height,
            "config": self.layout_manager.get_layout_config().__dict__
        }

    async def animate_content_change(self, old_content: Any, new_content: Any,
                                   animation_type: AnimationType = AnimationType.FADE_IN) -> Any:
        """Animate content changes"""
        try:
            if isinstance(old_content, Panel) and isinstance(new_content, Panel):
                return await self.animation_engine.animate_panel_transition(
                    old_content, new_content, animation_type
                )
            else:
                # For non-panel content, just return new content
                await self.animation_engine.animate_transition(
                    "content_change",
                    animation_type,
                    duration=0.2
                )
                return new_content

        except Exception as e:
            self.logger.error(f"Error animating content change: {e}")
            return new_content

    def set_performance_mode(self, high_performance: bool = True) -> None:
        """Set performance mode (disables animations for better performance)"""
        if high_performance:
            self.animation_engine.set_animation_speed(0.1)  # Very fast animations
            self.progressive_renderer.set_chunk_size(100)   # Larger chunks
            self.progressive_renderer.set_render_delay(0.001)  # Minimal delay
        else:
            self.animation_engine.set_animation_speed(1.0)   # Normal speed
            self.progressive_renderer.set_chunk_size(50)     # Normal chunks
            self.progressive_renderer.set_render_delay(0.01) # Normal delay