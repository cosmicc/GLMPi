from datetime import datetime
from time import perf_counter, process_time
from timeit import default_timer as timer

from loguru import logger as log


class codetime():
    def __init__(self, name):
        self.name = name
        self.starttime = datetime.now().timestamp()
        self.start_proctime = process_time()
        self.start_timeit = timer()
        self.start_perf = perf_counter()

    def stop(self, debug=False):
        self.elapsed = timer() - self.start_timeit
        if debug:
            log.warning(f'-------------------[ {self.name} Timer Results ]---------------------')
            log.warning(f'Process Time Elapsed: {process_time() - self.start_proctime} Seconds')
            log.warning(f'Datetime Elapsed: {datetime.now().timestamp() - self.starttime} Seconds')
            log.warning(f'Timer Time Elapsed: {self.elapsed} Seconds')
            log.warning(f'Perf timer Elapsed: {perf_counter() - self.start_perf}')
            log.warning('----------------------------------------------------------------------')
