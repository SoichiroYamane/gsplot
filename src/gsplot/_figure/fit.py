"""Figure-local fitting for independent gsplot text annotations."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from typing import Any, cast

from matplotlib.backend_bases import RendererBase
from matplotlib.figure import Figure
from matplotlib.text import Annotation, Text
from matplotlib.transforms import Bbox, ScaledTranslation, Transform

from .._core.errors import LayoutError

_FIGURE_FIT_STATE = "_gsplot_figure_fit_state"
_MAX_FIT_PASSES = 4
_DISPLAY_EPSILON = 1e-6


@dataclass(slots=True)
class _AnnotationRecord:
    """Base and last-applied placement for one registered annotation."""

    annotation_points: bool
    base_transform: Transform | None = None
    base_position: tuple[float, float] | None = None
    applied_transform: Transform | None = None
    applied_position: tuple[float, float] | None = None


@dataclass(slots=True)
class _FigureFitState:
    """Mutable annotation registry owned by one Figure."""

    annotations: dict[Text, _AnnotationRecord] = field(default_factory=dict)


def configure_figure_fit(
    figure: Figure,
    enabled: bool,
    *,
    reset: bool = False,
) -> None:
    """Configure one Figure's independent-text fitting policy."""

    if not enabled:
        setattr(figure, _FIGURE_FIT_STATE, None)
        return
    state = None if reset else getattr(figure, _FIGURE_FIT_STATE, None)
    if not isinstance(state, _FigureFitState):
        state = _FigureFitState()
    setattr(figure, _FIGURE_FIT_STATE, state)


def _figure_fit_state(figure: Figure) -> _FigureFitState | None:
    """Return the Figure-local fitting state when the policy is enabled."""

    state = getattr(figure, _FIGURE_FIT_STATE, None)
    return state if isinstance(state, _FigureFitState) else None


def _get_figure_renderer(figure: Figure) -> RendererBase:
    """Return the renderer for a Figure across Matplotlib backends."""

    try:
        return cast(RendererBase, cast(Any, figure)._get_renderer())
    except Exception as exc:
        raise LayoutError("could not determine the rendered Figure renderer") from exc


def _current_position(text: Text) -> tuple[float, float]:
    """Return a Text position as a finite two-dimensional tuple."""

    raw_position = tuple(text.get_position())
    if len(raw_position) != 2:
        raise LayoutError("figure_fit: annotation position is not two-dimensional")
    position = (float(raw_position[0]), float(raw_position[1]))
    if not all(math.isfinite(value) for value in position):
        raise LayoutError("figure_fit: annotation position is not finite")
    return position


def _capture_record(
    text: Text,
    annotation_points: bool,
    previous: _AnnotationRecord | None,
) -> _AnnotationRecord:
    """Capture caller placement while avoiding a previous fit translation."""

    if annotation_points:
        position = _current_position(text)
        if (
            previous is not None
            and previous.annotation_points
            and previous.applied_position is not None
            and position == previous.applied_position
        ):
            position = previous.base_position or position
        return _AnnotationRecord(
            annotation_points=True,
            base_position=position,
            applied_position=position,
        )

    transform = cast(Transform, text.get_transform())
    if (
        previous is not None
        and not previous.annotation_points
        and previous.applied_transform is transform
    ):
        transform = previous.base_transform or transform
    return _AnnotationRecord(
        annotation_points=False,
        base_transform=transform,
        applied_transform=transform,
    )


def _capture_location(
    text: Text,
    annotation_points: bool,
) -> Transform | tuple[float, float]:
    """Capture an artist's current position for transactional rollback."""

    return (
        _current_position(text)
        if annotation_points
        else cast(Transform, text.get_transform())
    )


def _restore_location(
    text: Text,
    annotation_points: bool,
    location: Transform | tuple[float, float],
) -> None:
    """Restore an artist's exact transform or point position."""

    if annotation_points:
        cast(Annotation, text).set_position(cast(tuple[float, float], location))
    else:
        text.set_transform(cast(Transform, location))


def register_figure_annotations(
    figure: Figure,
    annotations: Iterable[tuple[Text, bool]],
) -> None:
    """Register independent annotations and fit the complete Figure set."""

    state = _figure_fit_state(figure)
    if state is None:
        return
    items = tuple(annotations)
    previous_annotations = {
        text: replace(record) for text, record in state.annotations.items()
    }
    previous_locations: dict[Text, tuple[bool, Transform | tuple[float, float]]] = {
        text: (
            record.annotation_points,
            _capture_location(text, record.annotation_points),
        )
        for text, record in previous_annotations.items()
        if text.figure is figure
    }
    for text, annotation_points in items:
        if text.figure is figure and text not in previous_locations:
            previous_locations[text] = (
                annotation_points,
                _capture_location(text, annotation_points),
            )
    try:
        for text, annotation_points in items:
            if text.figure is figure:
                state.annotations[text] = _capture_record(
                    text,
                    annotation_points,
                    previous_annotations.get(text),
                )
        fit_figure_annotations(figure)
    except Exception:
        state.annotations.clear()
        state.annotations.update(previous_annotations)
        for text, (annotation_points, location) in previous_locations.items():
            _restore_location(text, annotation_points, location)
        raise


def _live_annotations(figure: Figure) -> tuple[tuple[Text, _AnnotationRecord], ...]:
    """Return visible registered annotations still attached to one Figure."""

    state = _figure_fit_state(figure)
    if state is None:
        return ()
    live: list[tuple[Text, _AnnotationRecord]] = []
    stale: list[Text] = []
    for text, record in state.annotations.items():
        if text.figure is not figure:
            stale.append(text)
        elif text.get_visible():
            live.append((text, record))
    for text in stale:
        del state.annotations[text]
    return tuple(live)


def _reset_annotation(text: Text, record: _AnnotationRecord) -> None:
    """Remove a previous fit translation while preserving the caller's base."""

    if record.annotation_points:
        if record.base_position is None:
            raise LayoutError("figure_fit: annotation has no base position")
        cast(Annotation, text).set_position(record.base_position)
        record.applied_position = record.base_position
        return

    if record.base_transform is None:
        raise LayoutError("figure_fit: annotation has no base transform")
    text.set_transform(record.base_transform)
    record.applied_transform = record.base_transform


def _annotation_box(text: Text, renderer: Any) -> Any:
    """Return one finite rendered text box or raise a layout error."""

    try:
        boxes = [text.get_window_extent(renderer)]
        patch = text.get_bbox_patch()
        if patch is not None and patch.get_visible():
            boxes.append(patch.get_window_extent(renderer))
        box = Bbox.union(boxes)
    except Exception as exc:
        raise LayoutError("figure_fit: could not measure an annotation") from exc
    values = (box.x0, box.y0, box.x1, box.y1)
    if not all(math.isfinite(float(value)) for value in values):
        raise LayoutError("figure_fit: annotation bounds are not finite")
    return box


def _required_shift(
    lower: float,
    upper: float,
    box_lower: float,
    box_upper: float,
    *,
    dimension: str,
) -> float:
    """Return the smallest display-space shift that enters one Figure edge."""

    if box_upper - box_lower > upper - lower + _DISPLAY_EPSILON:
        raise LayoutError(
            f"figure_fit: annotation does not fit within the Figure {dimension}"
        )
    if box_lower < lower:
        return lower - box_lower
    if box_upper > upper:
        return upper - box_upper
    return 0.0


def _shift_for(
    figure: Figure,
    text: Text,
    renderer: Any,
    *,
    record: _AnnotationRecord,
) -> tuple[float, float]:
    """Measure one base-position annotation and apply its minimum correction."""

    box = _annotation_box(text, renderer)
    figure_box = figure.bbox
    dx = _required_shift(
        figure_box.x0,
        figure_box.x1,
        box.x0,
        box.x1,
        dimension="width",
    )
    dy = _required_shift(
        figure_box.y0,
        figure_box.y1,
        box.y0,
        box.y1,
        dimension="height",
    )
    if dx == 0.0 and dy == 0.0:
        return dx, dy

    if record.annotation_points:
        if record.base_position is None:
            raise LayoutError("figure_fit: annotation has no base position")
        position = record.base_position
        points_per_display_unit = 72.0 / float(figure.dpi)
        applied_position = (
            float(position[0]) + dx * points_per_display_unit,
            float(position[1]) + dy * points_per_display_unit,
        )
        cast(Annotation, text).set_position(applied_position)
        record.applied_position = applied_position
    else:
        if record.base_transform is None:
            raise LayoutError("figure_fit: annotation has no base transform")
        record.applied_transform = record.base_transform + ScaledTranslation(
            dx / float(figure.dpi),
            dy / float(figure.dpi),
            figure.dpi_scale_trans,
        )
        text.set_transform(record.applied_transform)
    return dx, dy


def fit_figure_annotations(figure: Figure) -> None:
    """Keep registered independent annotations inside a fixed Figure canvas."""

    annotations = _live_annotations(figure)
    if not annotations:
        return
    canvas = cast(Any, figure.canvas)
    for _ in range(_MAX_FIT_PASSES):
        for text, record in annotations:
            _reset_annotation(text, record)
        try:
            canvas.draw()
            renderer = _get_figure_renderer(figure)
        except Exception as exc:
            raise LayoutError("figure_fit: could not render the Figure") from exc

        moved = False
        for text, record in annotations:
            dx, dy = _shift_for(
                figure,
                text,
                renderer,
                record=record,
            )
            moved = moved or dx != 0.0 or dy != 0.0
        if not moved:
            return

    try:
        canvas.draw()
        renderer = _get_figure_renderer(figure)
    except Exception as exc:
        raise LayoutError("figure_fit: could not render the Figure") from exc
    for text, _ in annotations:
        box = _annotation_box(text, renderer)
        figure_box = figure.bbox
        if (
            box.x0 < figure_box.x0 - _DISPLAY_EPSILON
            or box.y0 < figure_box.y0 - _DISPLAY_EPSILON
            or box.x1 > figure_box.x1 + _DISPLAY_EPSILON
            or box.y1 > figure_box.y1 + _DISPLAY_EPSILON
        ):
            raise LayoutError(
                "figure_fit: annotations could not be placed inside the Figure"
            )


__all__ = [
    "configure_figure_fit",
    "fit_figure_annotations",
    "register_figure_annotations",
]
