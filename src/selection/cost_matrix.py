from typing import List, Tuple
import multiprocessing as mp
from multiprocessing.dummy import Pool as ThreadPool


from src.animation.timeline import CreateTimeline, Timeline
from src.animation.time import Time
from src.animation.animation import Animation
from src.selection.cost_matrix_operation import CostMatrixOperation
from src.utils import IO, TransformStringsInList


class CostMatrix:
    def __init__(self, animation: Animation, operation: CostMatrixOperation):
        self.animation = animation
        self.operation = operation

        self.matrix = {}
        self._setup_matrix()

    def _setup_matrix(self) -> None:
        for timeline in self.animation.timeline.permutations():
            s = timeline.start.time
            e = timeline.end.time

            if s not in self.matrix.keys():
                self.matrix[s] = {e: (999999999.0, -1)}
            else:
                self.matrix[s][e] = (999999999.0, -1)

    def _run_calculation_on_timeline(self, timeline):
        s = timeline.start.time
        e = timeline.end.time
        frames = self.animation.get_frames(timeline)
        error, index = self.operation.calculate(frames)
        self.matrix[s][e] = (error, index)

    def _execute_operation(self) -> None:
        pool = ThreadPool(4)
        pool.map(self._run_calculation_on_timeline, self.animation.timeline.permutations())
        pool.close()
        pool.join()

    def value_of_max_error(self, timeline: Timeline) -> float:
        assert self.matrix != {}
        s = timeline.start.time
        e = timeline.end.time
        return self.matrix[s][e][0]

    def index_of_max_error(self, timeline: Timeline) -> float:
        assert self.matrix != {}
        s = timeline.start.time
        e = timeline.end.time
        return self.matrix[s][e][1]

    def as_csv(self) -> List[List[str]]:
        csv = [["i", "j", "max_error_value", "max_error_index"]]
        for timeline in self.animation.timeline.permutations():
            s = int(timeline.start.time)
            e = int(timeline.end.time)
            row = ["%d" % s, "%d" % e, "%2.8f" % self.value_of_max_error(timeline), "%d" % self.index_of_max_error(timeline)]
            csv.append(row)
        return csv

    def set(self, timeline: Timeline, error: float, index: int) -> None:
        s = int(timeline.start.time)
        e = int(timeline.end.time)
        self.matrix[s][e] = (error, index)

    @staticmethod
    def _get_data(filepath) -> Tuple[List[Timeline], List[float], List[int]]:
        csv = IO.read_csv_content_as_list_of_lists(filepath)

        data: List[List[float]] = [TransformStringsInList.as_floats(row) for row in csv[1:]]

        timelines = []
        values = []
        indices = []
        for row in data:
            s = int(row[0])
            e = int(row[1])
            timelines.append(CreateTimeline.from_start_end(Time(s), Time(e)))
            values.append(float(row[2]))
            indices.append(int(row[3]))

        return timelines, values, indices

    @staticmethod
    def from_csv(filepath: str, animation: Animation, operation: CostMatrixOperation):
        timelines, values, indices = CostMatrix._get_data(filepath)
        cost_matrix: CostMatrix = CostMatrix(animation, operation)
        for (timeline, value, index) in zip(timelines, values, indices):
            cost_matrix.set(timeline, value, index)
        return cost_matrix

    @staticmethod
    def from_animation(animation: Animation, operation: CostMatrixOperation):
        cost_matrix: CostMatrix = CostMatrix(animation, operation)
        cost_matrix._execute_operation()
        return cost_matrix

