from services.progress.combined_progress.particle_progress import ParticleProgress
from services.progress.task_progress import TaskProgress
from services.progress.combined_progress.process_particle import ProgressParticle


class CombinedProgress(TaskProgress):
    task_id: str
    _particle_progresses: dict[str, ParticleProgress]

    def __init__(self, task_id: str, particles: list[ProgressParticle]) -> None:
        self.task_id = task_id
        self._particle_progresses = {}
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

    def set_particle_value(self, key: str, value: float) -> None:
        self._particle_progresses[key].value = value
        self._update()
