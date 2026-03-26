from typing import Any, Dict, Optional

from flask import current_app

from blueprints.tool_highlight.socketio.rooms.task_progress import TaskProgressRoom

from services.progress.combined_progress.particle_progress import ParticleProgress
from services.progress.task_progress import TaskProgress
from services.progress.combined_progress.process_particle import ProgressParticle


class CombinedProgress(TaskProgress):
    task_id: str
    _particle_progresses: dict[str, ParticleProgress]
    _particle_descriptions: dict[str, str]
    _active_particle_key: Optional[str]

    def __init__(self, task_id: str, particles: list[ProgressParticle]) -> None:
        self.task_id = task_id
        self._particle_progresses = {}
        self._particle_descriptions = {}
        self._active_particle_key = None
        total_max: float = 0.0

        for particle in particles:
            if particle.key in self._particle_progresses:
                raise ValueError('Duplicate progress key.')

            particle_max: float = (
                float(particle.max_value) if particle.max_value is not None else 100.0
            )
            total_max += particle_max
            self._particle_progresses[particle.key] = ParticleProgress(
                value=0,
                max_value=particle_max,
            )
            self._particle_descriptions[particle.key] = (
                (particle.description or '').strip()
            )

        super().__init__(task_id, int(total_max))
        self._update()

    def add_particle(self, particle: ProgressParticle) -> None:
        if particle.key in self._particle_progresses:
            raise ValueError('Duplicate progress key.')

        particle_max: float = (
            float(particle.max_value) if particle.max_value is not None else 100.0
        )

        self._particle_progresses[particle.key] = ParticleProgress(
            value=0,
            max_value=particle_max,
        )
        self._particle_descriptions[particle.key] = (
            (particle.description or '').strip()
        )

        total_max: int = int(
            sum(pp.max_value for pp in self._particle_progresses.values())
        )
        self._set_max_value(total_max)
        self._update()

    def _update(self):
        # [start] summarize metrics
        total_value = 0
        total_max_value = 0

        for particle_progress in self._particle_progresses.values():
            total_value += particle_progress.value
            total_max_value += particle_progress.max_value
        # [end]

        self._set_value(total_value)
        self._set_max_value(total_max_value)
        self._send_progress_event()

    def _phase_description_for_active_particle(self) -> Optional[str]:
        if self._active_particle_key is None:
            return None

        text: str = self._particle_descriptions.get(self._active_particle_key, '')

        return text if text else None

    def _send_progress_event(self) -> None:
        progress_value: float = self.getProgress()
        phase_description: Optional[str] = self._phase_description_for_active_particle()
        payload: Dict[str, Any] = {
            'task_id': self.task_id,
            'progress': progress_value,
        }

        if phase_description is not None:
            payload['phase_description'] = phase_description

        socketio = current_app.extensions.get('socketio')
        socketio.emit(
            'progress',
            payload,
            room=TaskProgressRoom.get_room_name(self.task_id),
        )

    def set_particle_value(self, key: str, value: float) -> None:
        self._active_particle_key = key
        self._particle_progresses[key].value = value
        self._update()
