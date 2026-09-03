from time import monotonic


class TenantCache:
    def __init__(self, ttl, clock=monotonic):
        if ttl < 0:
            raise ValueError("ttl must be non-negative")
        self.ttl = ttl
        self.clock = clock
        self.entries = {}

    def get(self, tenant, key, loader):
        if self.ttl == 0:
            return loader()

        cache_key = (tenant, key)
        entry = self.entries.get(cache_key)
        if entry is not None:
            value, expires_at = entry
            if self.clock() < expires_at:
                return value

        value = loader()
        self.entries[cache_key] = (value, self.clock() + self.ttl)
        return value
