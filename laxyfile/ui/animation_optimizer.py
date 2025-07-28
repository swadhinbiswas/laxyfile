"""
Animation Optimizer

Optimized animation system for LaxyFile UI with smooth transitions,
performance monitoring, and adaptive quality settings.
"""

import time
import asyncio
from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from rich.text import Text
from rich.style import Style
from rich.color import Color

from ..utils.logger import Logger


class AnimationType(Enum):
    """Types of animations"""
    FADE = "fade"
    SLIDE = "slide"
    SCALE = "scale"
    COLOR_TRANSITION = "color_transition"
    CURSOR_BLINK = "cursor_blink"
    PROGRESS = "progress"
    LOADING_SPINNER = "loading_spinner"


class AnimationQuality(Enum):
    """Animation quality levels"""
    HIGH = "high"      # 60 FPS, full effects
    MEDIUM = "medium"  # 30 FPS, reduced effects
    LOW = "low"        # 15 FPS, minimal effects
    DISABLED = "disabled"  # No animations


@dataclass
class AnimationConfig:
    """Configuration for animations"""
    quality: AnimationQuality = AnimationQuality.MEDIUM
    max_fps: int = 30
    enable_transitions: bool = True
    enable_cursor_animations: bool = True
    enable_loading_animations: bool = True
    adaptive_quality: bool = True
    performance_threshold_ms: float = 16.67  # 60 FPS threshold


@dataclass
class AnimationFrame:
    """Single animation frame"""
    timestamp: float
    content: Any
    style: Optional[Style] = None
    alpha: float = 1.0


@dataclass
class Animation:
    """Animation definition"""
    animation_id: str
    animation_type: AnimationType
    duration: float
    frames: List[AnimationFrame] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    loop: bool = False
    easing_function: Optional[Callable[[float], float]] = None
    on_complete: Optional[Callable] = None
    is_active: bool = False


class EasingFunctions:
    """Collection of easing functions for smooth animations"""

    @staticmethod
    def linear(t: float) -> float:
        """Linear easing"""
        return t

    @staticmethod
    def ease_in_quad(t: float) -> float:
        """Quadratic ease-in"""
        return t * t

    @staticmethod
    def ease_out_quad(t: float) -> float:
        """Quadratic ease-out"""
        return 1 - (1 - t) * (1 - t)

    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """Quadratic ease-in-out"""
        if t < 0.5:
            return 2 * t * t
        return 1 - 2 * (1 - t) * (1 - t)

    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """Cubic ease-in"""
        return t * t * t

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Cubic ease-out"""
        return 1 - (1 - t) ** 3

    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Cubic ease-in-out"""
        if t < 0.5:
            return 4 * t * t * t
        return 1 - 4 * (1 - t) ** 3

    @staticmethod
    def bounce_out(t: float) -> float:
        """Bounce ease-out"""
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375


class ColorAnimator:
    """Specialized color animation utilities"""

    @staticmethod
    def interpolate_color(color1: str, color2: str, t: float) -> str:
        """Interpolate between two colors"""
        try:
            # Parse colors
            c1 = Color.parse(color1)
            c2 = Color.parse(color2)

            if hasattr(c1, 'triplet') and hasattr(c2, 'triplet'):
                # RGB interpolation
                r1, g1, b1 = c1.triplet
                r2, g2, b2 = c2.triplet

                r = int(r1 + (r2 - r1) * t)
                g = int(g1 + (g2 - g1) * t)
                b = int(b1 + (b2 - b1) * t)

                return f"rgb({r},{g},{b})"
            else:
                # Fallback to original colors
                return color2 if t > 0.5 else color1

        except Exception:
            return color2 if t > 0.5 else color1

    @staticmethod
    def create_gradient_frames(start_color: str, end_color: str,
                             frame_count: int) -> List[str]:
        """Create gradient color frames"""
        frames = []
        for i in range(frame_count):
            t = i / (frame_count - 1) if frame_count > 1 else 0
            color = ColorAnimator.interpolate_color(start_color, end_color, t)
            frames.append(color)
        return frames


class AnimationOptimizer:
    """Main animation optimization system"""

    def __init__(self, config: AnimationConfig):
        self.config = config
        self.logger = Logger()

        # Animation state
        self.active_animations: Dict[str, Animation] = {}
        self.animation_queue: List[Animation] = []
        self.last_frame_time = time.time()
        self.frame_times: List[float] = []

        # Performance tracking
        self.performance_stats = {
            'frames_rendered': 0,
            'average_frame_time': 0.0,
            'dropped_frames': 0,
            'quality_adjustments': 0
        }

        # Quality adaptation
        self.current_quality = config.quality
        self.last_quality_check = time.time()

        # Pre-built animations
        self._spinner_frames = self._create_spinner_frames()
        self._cursor_blink_frames = self._create_cursor_blink_frames()

    def create_fade_animation(self, animation_id: str, content: Any,
                            duration: float = 0.5, fade_in: bool = True) -> Animation:
        """Create fade animation"""
        animation = Animation(
            animation_id=animation_id,
            animation_type=AnimationType.FADE,
            duration=duration,
            easing_function=EasingFunctions.ease_out_quad
        )

        # Generate frames
        frame_count = max(5, int(duration * self._get_target_fps()))
        for i in range(frame_count):
            t = i / (frame_count - 1) if frame_count > 1 else 0
            alpha = t if fade_in else 1 - t

            frame = AnimationFrame(
                timestamp=t * duration,
                content=content,
                alpha=alpha
            )
            animation.frames.append(frame)

        return animation

    def create_slide_animation(self, animation_id: str, content: Any,
                             start_pos: Tuple[int, int], end_pos: Tuple[int, int],
                             duration: float = 0.3) -> Animation:
        """Create slide animation"""
        animation = Animation(
            animation_id=animation_id,
            animation_type=AnimationType.SLIDE,
            duration=duration,
            easing_function=EasingFunctions.ease_out_cubic
        )

        # Generate frames
        frame_count = max(5, int(duration * self._get_target_fps()))
        start_x, start_y = start_pos
        end_x, end_y = end_pos

        for i in range(frame_count):
            t = i / (frame_count - 1) if frame_count > 1 else 0
            if animation.easing_function:
                t = animation.easing_function(t)

            x = int(start_x + (end_x - start_x) * t)
            y = int(start_y + (end_y - start_y) * t)

            frame = AnimationFrame(
                timestamp=t * duration,
                content=content,
                # Position would be handled by the renderer
            )
            animation.frames.append(frame)

        return animation

    def create_color_transition(self, animation_id: str, text: str,
                              start_color: str, end_color: str,
                              duration: float = 0.4) -> Animation:
        """Create color transition animation"""
        animation = Animation(
            animation_id=animation_id,
            animation_type=AnimationType.COLOR_TRANSITION,
            duration=duration,
            easing_function=EasingFunctions.ease_in_out_quad
        )

        # Generate color frames
        frame_count = max(5, int(duration * self._get_target_fps()))
        colors = ColorAnimator.adient_frames(start_color, end_color, frame_count)

        for i, color in enumerate(colors):
            t = i / (frame_count - 1) if frame_count > 1 else 0

            styled_text = Text(text, style=Style(color=color))
            frame = AnimationFrame(
                timestamp=t * duration,
                content=styled_text
            )
            animation.frames.append(frame)

        return animation

    def create_loading_spinner(self, animation_id: str, duration: float = 2.0) -> Animation:
        """Create loading spinner animation"""
        animation = Animation(
            animation_id=animation_id,
            animation_type=AnimationType.LOADING_SPINNER,
            duration=duration,
            loop=True
        )

        # Use pre-built spinner frames
        frame_duration = duration / len(self._spinner_frames)
        for i, spinner_char in enumerate(self._spinner_frames):
            frame = AnimationFrame(
                timestamp=i * frame_duration,
                content=Text(spinner_char, style=Style(color="cyan"))
            )
            animation.frames.append(frame)

        return animation

    def create_cursor_blink(self, animation_id: str, cursor_char: str = "█") -> Animation:
        """Create cursor blink animation"""
        animation = Animation(
            animation_id=animation_id,
            animation_type=AnimationType.CURSOR_BLINK,
            duration=1.0,
            loop=True
        )

        # Visible and invisible states
        visible_frame = AnimationFrame(
            timestamp=0.0,
            content=Text(cursor_char, style=Style(color="white"))
        )
        invisible_frame = AnimationFrame(
            timestamp=0.5,
            content=Text(" ")
        )

        animation.frames.extend([visible_frame, invisible_frame])
        return animation

    def start_animation(self, animation: Animation) -> None:
        """Start an animation"""
        if self.current_quality == AnimationQuality.DISABLED:
            return

        animation.start_time = time.time()
        animation.end_time = animation.start_time + animation.duration
        animation.is_active = True

        self.active_animations[animation.animation_id] = animation
        self.logger.debug(f"Started animation: {animation.animation_id}")

    def stop_animation(self, animation_id: str) -> None:
        """Stop an animation"""
        if animation_id in self.active_animations:
            animation = self.active_animations[animation_id]
            animation.is_active = False

            if animation.on_complete:
                try:
                    animation.on_complete()
                except Exception as e:
                    self.logger.error(f"Error in animation completion callback: {e}")

            del self.active_animations[animation_id]
            self.logger.debug(f"Stopped animation: {animation_id}")

    def update_animations(self) -> Dict[str, Any]:
        """Update all active animations and return current frames"""
        current_time = time.time()
        frame_start = current_time

        if self.current_quality == AnimationQuality.DISABLED:
            return {}

        # Check if we should render this frame
        target_fps = self._get_target_fps()
        min_frame_time = 1.0 / target_fps

        if current_time - self.last_frame_time < min_frame_time:
            return {}  # Skip frame to maintain target FPS

        current_frames = {}
        completed_animations = []

        for animation_id, animation in self.active_animations.items():
            if not animation.is_active:
                continue

            # Calculate animation progress
            elapsed = current_time - animation.start_time
            progress = min(elapsed / animation.duration, 1.0)

            # Apply easing function
            if animation.easing_function:
                eased_progress = animation.easing_function(progress)
            else:
                eased_progress = progress

            # Find current frame
            current_frame = self._get_frame_at_progress(animation, eased_progress)
            if current_frame:
                current_frames[animation_id] = current_frame

            # Check if animation is complete
            if progress >= 1.0:
                if animation.loop:
                    # Restart looping animation
                    animation.start_time = current_time
                else:
                    completed_animations.append(animation_id)

        # Clean up completed animations
        for animation_id in completed_animations:
            self.stop_animation(animation_id)

        # Update performance stats
        frame_time = time.time() - frame_start
        self._update_performance_stats(frame_time)

        # Adaptive quality adjustment
        if self.config.adaptive_quality:
            self._adjust_quality_if_needed()

        self.last_frame_time = current_time
        return current_frames

    def _get_frame_at_progress(self, animation: Animation, progress: float) -> Optional[AnimationFrame]:
        """Get animation frame at specific progress"""
        if not animation.frames:
            return None

        # Find the appropriate frame
        target_time = progress * animation.duration

        for i, frame in enumerate(animation.frames):
            if frame.timestamp <= target_time:
                # Check if this is the last frame or if next frame is beyond target
                if i == len(animation.frames) - 1 or animation.frames[i + 1].timestamp > target_time:
                    return frame

        # Fallback to last frame
        return animation.frames[-1] if animation.frames else None

    def _get_target_fps(self) -> int:
        """Get target FPS based on current quality"""
        fps_map = {
            AnimationQuality.HIGH: 60,
            AnimationQuality.MEDIUM: 30,
            AnimationQuality.LOW: 15,
            AnimationQuality.DISABLED: 0
        }
        return min(fps_map.get(self.current_quality, 30), self.config.max_fps)

    def _update_performance_stats(self, frame_time: float) -> None:
        """Update performance statistics"""
        self.performance_stats['frames_rendered'] += 1
        self.frame_times.append(frame_time)

        # Keep only recent frame times
        if len(self.frame_times) > 100:
            self.frame_times = self.frame_times[-50:]

        # Calculate average frame time
        if self.frame_times:
            self.performance_stats['average_frame_time'] = sum(self.frame_times) / len(self.frame_times)

        # Check for dropped frames
        target_frame_time = 1.0 / self._get_target_fps()
        if frame_time > target_frame_time * 1.5:
            self.performance_stats['dropped_frames'] += 1

    def _adjust_quality_if_needed(self) -> None:
        """Adjust animation quality based on performance"""
        current_time = time.time()

        # Check quality every 2 seconds
        if current_time - self.last_quality_check < 2.0:
            return

        self.last_quality_check = current_time

        if len(self.frame_times) < 10:
            return

        avg_frame_time = sum(self.frame_times[-10:]) / 10
        target_frame_time = 1.0 / self._get_target_fps()

        # Reduce quality if performance is poor
        if avg_frame_time > target_frame_time * 2:
            if self.current_quality == AnimationQuality.HIGH:
                self.current_quality = AnimationQuality.MEDIUM
                self.performance_stats['quality_adjustments'] += 1
                self.logger.info("Reduced animation quality to MEDIUM")
            elif self.current_quality == AnimationQuality.MEDIUM:
                self.current_quality = AnimationQuality.LOW
                self.performance_stats['quality_adjustments'] += 1
                self.logger.info("Reduced animation quality to LOW")

        # Increase quality if performance is good
        elif avg_frame_time < target_frame_time * 0.5:
            if self.current_quality == AnimationQuality.LOW:
                self.current_quality = AnimationQuality.MEDIUM
                self.performance_stats['quality_adjustments'] += 1
                self.logger.info("Increased animation quality to MEDIUM")
            elif self.current_quality == AnimationQuality.MEDIUM and self.config.quality == AnimationQuality.HIGH:
                self.current_quality = AnimationQuality.HIGH
                self.performance_stats['quality_adjustments'] += 1
                self.logger.info("Increased animation quality to HIGH")

    def _create_spinner_frames(self) -> List[str]:
        """Create spinner animation frames"""
        return ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def _create_cursor_blink_frames(self) -> List[str]:
        """Create cursor blink frames"""
        return ["█", " "]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get animation performance statistics"""
        stats = self.performance_stats.copy()
        stats.update({
            'current_quality': self.current_quality.value,
            'target_fps': self._get_target_fps(),
            'active_animations': len(self.active_animations),
            'recent_frame_times': self.frame_times[-10:] if self.frame_times else []
        })
        return stats

    def set_quality(self, quality: AnimationQuality) -> None:
        """Set animation quality"""
        self.current_quality = quality
        self.config.quality = quality
        self.logger.info(f"Animation quality set to: {quality.value}")

    def clear_all_animations(self) -> None:
        """Clear all active animations"""
        for animation_id in list(self.active_animations.keys()):
            self.stop_animation(animation_id)

    def is_animation_active(self, animation_id: str) -> bool:
        """Check if animation is active"""
        return animation_id in self.active_animations and self.active_animations[animation_id].is_active

    async def animate_text_typing(self, animation_id: str, text: str,
                                duration: float = 1.0) -> Animation:
        """Create typing animation for text"""
        animation = Animation(
            animation_id=animation_id,
            animation_type=AnimationType.FADE,  # Reusing fade type
            duration=duration
        )

        # Create frames for each character
        frame_count = len(text)
        if frame_count == 0:
            return animation

        char_duration = duration / frame_count

        for i in range(frame_count + 1):
            visible_text = text[:i]
            cursor = "█" if i < frame_count else ""

            frame = AnimationFrame(
                timestamp=i * char_duration,
                content=Text(visible_text + cursor, style=Style(color="white"))
            )
            animation.frames.append(frame)

        return animation

    def create_progress_animation(self, animation_id: str, width: int = 20,
                                progress: float = 0.0) -> Animation:
        """Create progress bar animation"""
        animation = Animation(
            animation_id=animation_id,
            animation_type=AnimationType.PROGRESS,
            duration=0.1,  # Quick update
        )

        filled = int(progress * width)
        empty = width - filled

        progress_bar = "█" * filled + "░" * empty
        percentage = f" {progress * 100:.1f}%"

        frame = AnimationFrame(
            timestamp=0.0,
            content=Text(progress_bar + percentage, style=Style(color="cyan"))
        )
        animation.frames.append(frame)

        return animation