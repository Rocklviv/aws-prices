import threading
from time import time
from collections import OrderedDict

__all__ = ['CachedObject', 'CacheController', 'CacheException']


class CacheException(Exception):
    """
    Generic Cache Exception
    """
    pass


class CachedObject(object):
    """
    """
    def __init__(self, name, obj, ttl=60):
        self.hits = 0
        self.name = name
        self.obj = obj
        self.ttl = ttl
        self.timestamp = time()


class CacheController(object):
    def __init__(self, maxsize=0, housekeeping=0):
        """
        Initializes a new cache inventory

        Args:
            maxsize      (int): Upperbound limit on the number of items
                                that will be stored in the cache inventory
            housekeeping (int): Time in minutes to perform periodic
                                cache housekeeping

        """
        if maxsize < 0:
            raise CacheException('Cache inventory size cannot be negative')

        if housekeeping < 0:
            raise CacheException('Cache housekeeping period cannot be negative')

        self._cache = OrderedDict()
        self.maxsize = maxsize
        self.housekeeping = housekeeping * 60.0
        self.lock = threading.RLock()

        if self.housekeeping > 0:
            threading.Timer(self.housekeeping, self.housekeeper).start()

    def __len__(self):
        with self.lock:
            return len(self._cache)

    def __contains__(self, key):
        with self.lock:
            if key not in self._cache:
                return False

            item = self._cache[key]
            if self._has_expired(item):
                return False
            return True

    def _has_expired(self, item):
        """
        Checks if a cached item has expired and removes it if needed

        If the upperbound limit has been reached then the last item
        is being removed from the inventory.

        Args:
            item (CachedObject): A cached object to lookup

        """
        with self.lock:
            if time() > item.timestamp + item.ttl:
                self._cache.pop(item.name)
                return True
            return False

    def add(self, obj):
        """
        Add an item to the cache inventory

        Args:
            obj (CachedObject): A CachedObject instance to be added

        Raises:
            CacheException

        """
        if not isinstance(obj, CachedObject):
            raise Exception('Need a CachedObject instance to add in the cache')

        with self.lock:
            if self.maxsize > 0 and len(self._cache) == self.maxsize:
                popped = self._cache.popitem(last=False)
            self._cache[obj.name] = obj

    def get(self, key):
        """
        Retrieve an object from the cache inventory

        Args:
            key (str): Name of the cache item to retrieve

        Returns:
            The cached object if found, None otherwise

        """
        with self.lock:
            if key not in self._cache:
                return None

            item = self._cache[key]
            if self._has_expired(item):
                return None

            item.hits += 1
            return item.obj

    def housekeeper(self):
        """
        Remove expired entries from the cache on regular basis

        """
        with self.lock:
            expired = 0
            for name, item in self._cache.items():
                if self._has_expired(item):
                    expired += 1
            if self.housekeeping > 0:
                threading.Timer(self.housekeeping, self.housekeeper).start()