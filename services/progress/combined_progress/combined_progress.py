from services.progress.combined_progress.particle_progress import ParticleProgress
from services.progress.task_progress import TaskProgress
from services.progress.combined_progress.process_particle import ProgressParticle


class CombinedProgress(TaskProgress):
    task_id: str
    _particle_progresses: dict[str, ParticleProgress] = {}

    def __init__(self, task_id, particles: list[ProgressParticle]):
        self.task_id = task_id
        max_value = 0

        for particle in particles:
            self.add_particle(particle)
            max_value += particle.max_value

        super().__init__(task_id, max_value)
        self._update()

    def add_particle(self, particle: ProgressParticle):
        if particle.key in self._particle_progresses:
            raise ValueError('Duplicate progress key.')

        self._particle_progresses[particle.key] = ParticleProgress(
            value=0,
            max_value=particle.max_value,
        )

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
