import asyncio


class JobRunner:
    def __init__(self, resource):
        self.resource = resource
        self._tasks = set()
        self._closed = False
        self._close_task = None

    def start(self, coroutine):
        if self._closed:
            coroutine.close()
            raise RuntimeError("JobRunner is closed")
        task = asyncio.create_task(coroutine)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def close(self):
        if self._close_task is None:
            self._closed = True
            self._close_task = asyncio.create_task(self._close())
        # Cancelling a close caller must not interrupt the shared cleanup.
        await asyncio.shield(self._close_task)

    async def _close(self):
        tasks = tuple(self._tasks)
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await self.resource.aclose()
