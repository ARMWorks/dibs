from collections import UserDict

class MultiDict(UserDict):
    def __init__(*args, **kwargs):
        if not args:
            raise TypeError

        self, *args = args
        if len(args) > 1:
            raise TypeError

        self.__items = []
        self.__update(*args, **kwargs)

    __marker = object()

    def __update(self, *args, **kwargs):
        if len(args) > 1:
            raise ValueError
        if len(args) > 0:
            for arg in args[0]:
                key, value = arg
                self[key] = value
        for key, value in kwargs:
            self[key] = value

    def __setitem__(self, key, value):
        index = self.index(key)
        if index == None:
            self.__items.append((key, value))
            return
        self.__items[index] = (key, value)

    def __getitem__(self, key):
        value = self.get(key, self.__marker)
        if value == self.__marker:
            raise KeyError
        return value

    def __delitem__(self, key):
        for item in self.__items:
            _key, _ = item
            if _key == key:
                pass

    def __iter__(self):
        i = 0
        while i < len(self.__items):
            yield self.__items[i][0]
            i += 1

    def __clear__(self):
        self.__items = []

    def __contains__(self, key):
        for item in self.__items:
            _key, _ = item
            if _key == key:
                return True
        return False

    def __len__(self):
        return len(self.__items)

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self.items()))

    def keys(self):
        for item in self.__items:
            key, _ = item
            yield key

    def items(self):
        for item in self.__items:
            yield item

    def values(self):
        for item in self.__items:
            _, value = item
            yield value

    def get(self, key, default=None):
        for item in self.__items:
            _key, value = item
            if _key == key:
                return value
        return default

    def pop(self, key, default=__marker):
        for index, item in enumerate(self.__items[:]):
            _key, value = item
            if _key == key:
                del self.__items[index]
                return value
        if default is self.__marker:
            raise KeyError(key)
        return default

    def setdefault(self, key, default=None):
        for item in self.__items[:]:
            _key, value = item
            if _key == key:
                return value
        self.__items.append((key, default))
        return default

    def copy(self):
        return self.__class__(self)

    def index(self, key=__marker, value=__marker):
        if key == self.__marker and value == self.__marker:
            raise ValueError('key and/or value must be specified')

        for index, item in enumerate(self.__items):
            _key, _value = item
            if _key == self.__marker:
                if _value == value:
                    return index
            elif _key == key:
                if value == self.__marker:
                    return index
                elif _value == value:
                    return index
        return None

    def append(self, key, value):
        self.__items.append((key, value))

    def insert(self, index, key, value):
        self.__items.insert(index, (key, value))
