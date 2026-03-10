from typing import Union


class Interval:
    def __init__(self, begin, end):
        if begin > end:
            self.begin = end
            self.end = begin
        else:
            self.begin = begin
            self.end = end

    def __eq__(self, other: Interval):
        return self.begin == other.begin and self.end == other.end

    def __repr__(self):
        return f"Interval({self.begin}, {self.end})"

    def __hash__(self) -> int:
        return hash((self.begin, self.end))

    def intersection(self, other: 'Interval') -> Union['Interval', None]:
        begin1 = self.begin
        end1 = self.end
        begin2 = other.begin
        end2 = other.end

        if begin1 > end2 or end1 < begin2:
            return None

        i_begin = max(begin1, begin2)
        i_end = min(end1, end2)

        return Interval(i_begin, i_end)

    def intersects(self, other: 'Interval') -> bool:
        return self.intersection(other) is not None

    def union(self, other: 'Interval') -> Union['Interval', None]:
        if self.intersects(other) is None:
            return None

        return Interval(min(self.begin, other.begin), max(self.end, other.end))
