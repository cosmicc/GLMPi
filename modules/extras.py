from threads.threadqueues import strip_queue, status_queue
from time import sleep
import logging
from socket import gethostname

host_name = gethostname()
log = logging.getLogger(name=host_name)

def str2bool(v):
  return str(v).lower() in ("yes", "true", "t", "1")

def float_trunc_1dec(num):
    try:
        tnum = num // 0.1 / 10
    except:
        return False
    else:
        return tnum

def c2f(c):
    return float_trunc_1dec((c*9/5)+32)

def End(why):
    log.critical(f'Exiting: {why}')
    status_queue.put({'color': 'red', 'flashes': 3, 'flashrate': 'fast'})
    sleep(0.5)
    strip_queue.put((0, 'stripoff'),)
    sleep(0.2)
    exit(0)
