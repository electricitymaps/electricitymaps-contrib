from typing import List, NewType, Tuple

# BoundingBoxes indicate a geographic area of a zone.
# An example bounding box looks like: [[140.46, -39.64], [150.47, -33.48]],
# representing a box with corners at 140.46°E, 39.64°S and 150.47°E, 33.48°S.
Point = NewType("Point", Tuple[float, float])
BoundingBox = NewType("BoundingBox", List[Point])
