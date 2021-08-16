from ..domain.state import ObjectState2D

class SearchRegion:
    """domain-specific / abstraction-specific host of a set of locations. All that
    it needs to support is enumerability (which could technically be implemented
    by sampling)
    """
    def __init__(self, locations):
        self.locations = locations

    def __iter__(self):
        return iter(self.locations)

    def __contains__(self, item):
        return item in self.locations

    def object_state(self, objid, objclass, loc):
        raise NotImplementedError


class SearchRegion2D(SearchRegion):
    def __init__(self, locations):
        """
        locations should be 2D tuples of integers.
        """
        super().__init__(locations)
        self._w = max(locations, key=lambda l: l[0])[0] - min(locations, key=lambda l: l[0])[0] + 1
        self._l = max(locations, key=lambda l: l[1])[1] - min(locations, key=lambda l: l[1])[1] + 1

    def object_state(self, objid, objclass, loc):
        return ObjectState2D(objid, objclass, loc)

    @property
    def dim(self):
        return (self._w, self._l)

    @property
    def width(self):
        return self._w

    @property
    def length(self):
        return self._l
