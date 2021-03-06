from typing import List, Tuple

import numpy as np

from src.animation.frame import Frame
from src.animation.timeline import Timeline
from src.scene.coordinates.coordinate import Coordinate
from src.scene.coordinates.joint import Joint
from src.scene.coordinates.value import Value
from src.scene.things.character import Character
from src.scene.things.thing import Thing
from src.types import Time
from src.utils import IO, TransformStringsInList, TransformFloatsInList


class Animation:
    def __init__(self, name: str, timeline: Timeline, frames: List[Frame]):
        self.name = name
        self.timeline = timeline
        self.frames = frames

    def get_n_frames(self):
        s = int(self.timeline.start)
        e = int(self.timeline.end)
        return e - s + 1

    def get_frames(self, timeline: Timeline):
        anim_start_time = int(self.timeline.start)
        s = int(timeline.start)
        e = int(timeline.end)
        return [self.frames[i - anim_start_time] for i in range(s, e + 1)]

    def get_curve_for_dimension(self, name: str):
        curve: List[np.array] = []

        for index, frame in enumerate(self.frames):
            point = frame.as_point()
            value = point[self.get_index_of_dimension(name)]
            point_for_curve = np.array([self.timeline.start + index, value])
            curve.append(point_for_curve)

        return curve

    def dimensions(self) -> List[str]:
        dimensions = ["time"]
        first_thing: Thing = self.frames[0].things[0]
        for coordinate in first_thing.coordinates:
            for value in coordinate.values:
                dimensions.append(value.name)
        return dimensions

    def get_index_of_dimension(self, name: str) -> int:
        assert name != "time"

        first_thing: Thing = self.frames[0].things[0]

        i: int = 1
        for coordinate in first_thing.coordinates:
            for value in coordinate.values:
                if value.name == name:
                    return i
                else:
                    i += 1

        return i

    def value_matrix(self) -> List[List[float]]:
        matrix = []

        times = self.timeline.as_range()
        for (time, frame) in zip(times, self.frames):
            values: List[Value] = []
            first_thing: Thing = frame.things[0]
            for coordinate in first_thing.coordinates:
                values += coordinate.values

            row = [item.value for item in values]
            row_with_time = [time] + row
            matrix.append(row_with_time)

        return matrix

    def as_csv(self) -> List[List[str]]:
        dimensions: List[str] = self.dimensions()
        data: List[List[str]] = [TransformFloatsInList.as_strings(row) for row in self.value_matrix()]
        return [dimensions] + data

    @staticmethod
    def _get_data(filepath) -> Tuple[List[Time], List[List[Value]]]:
        csv = IO.read_csv_content_as_list_of_lists(filepath)

        dimensions: List[str] = csv[0]
        data: List[List[float]] = [TransformStringsInList.as_floats(row) for row in csv[1:]]

        times = []
        values = []
        for row in data:
            assert dimensions[0] == "time"
            times.append(int(row[0]))
            values.append([Value(name, value) for (name, value) in zip(dimensions[1:], row[1:])])

        return times, values

    @staticmethod
    def _organise_values_into_coordinates(values: List[Value]) -> List[Coordinate]:
        coordinates = []

        last_value_name = values[0].name
        sublist_of_values = []
        for value in values:
            curr_value_name = value.name
            if last_value_name.split("-")[0] != curr_value_name.split("-")[0]:
                coordinate: Coordinate = Joint(sublist_of_values)
                coordinates.append(coordinate)
                sublist_of_values = []
            sublist_of_values.append(value)

        # Put in the last coordinate
        if sublist_of_values:
            coordinate: Coordinate = Joint(sublist_of_values)
            coordinates.append(coordinate)

        return coordinates

    @staticmethod
    def _construct_thing_from_values(values: List[Value]) -> Thing:
        coordinates = Animation._organise_values_into_coordinates(values)
        return Character(None, [], coordinates)

    @staticmethod
    def character_animation_from_csv(filepath: str):
        name = filepath.split("/")[-1].split(".csv")[0]
        times, values = Animation._get_data(filepath)

        timeline = Timeline.from_times(times)

        frames: List[Frame] = []
        for (time, value) in zip(times, values):
            thing = Animation._construct_thing_from_values(value)
            frame = Frame(time, [thing])
            frames.append(frame)

        animation = Animation(name, timeline, frames)
        return animation
