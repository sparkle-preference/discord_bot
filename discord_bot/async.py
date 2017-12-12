import asyncio
import logging

DEBUG_LOG = logging.getLogger('debug')


class LoopManager:

    def __init__(self, *coros):
        self.loop = asyncio.get_event_loop()
        DEBUG_LOG.debug('Setting up coroutines')
        for coro in coros:
            self._add_to_loop(coro)

    def _add_to_loop(self, coro):
        try:
            DEBUG_LOG.debug("Add '%s' to the event loop", str(coro))
            asyncio.ensure_future(coro(), loop=self.loop)
        except:
            DEBUG_LOG.error("Unable to add %s to the event loop", str(coro))

    def start(self):
        try:
            self.loop.run_forever()
        except (KeyboardInterrupt, SystemExit, ConnectionError):
            DEBUG_LOG.exception("Loop error")
            raise
