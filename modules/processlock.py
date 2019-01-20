import os
import sys
import time
import fcntl
from loguru import logging
import atexit
import socket
import stat

host_name = socket.gethostname()
log = logging.getLogger(name=host_name)

mode = mode = 0o600 | stat.S_IRUSR


class plock:
    def __init__(self):
        if os.access('/run', os.W_OK) and os.path.isdir('/run'):
            lpath = '/run'
        else:
            log.critical('Cannot find a valid place to put the lockfile. Exiting')
            exit(1)

        self.ppid = str(os.getpid())
        self.progname = os.path.basename(sys.argv[0])
        self.lockfile = f'{lpath}/{self.progname}.pid'
        if not os.path.isfile(self.lockfile):
            os.mknod(self.lockfile, mode=mode)
        self.lock_handle = open(self.lockfile, 'w')

    def lock(self, retry=0):
        def aquireLock(self):
            try:
                fcntl.lockf(self.lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                return False
            except:
                log.exception('General error trying to lock process to file {}. exiting.'.format(self.ockfile))
                exit(1)
            else:
                log.debug('Process has been locked to file {} with PID [{}]'.format(self.lockfile, self.ppid))
                return True
        if aquireLock(self):
            self.lock_handle.write(self.ppid)
            self.lock_handle.close()
            atexit.register(self.unlock)
            return True
        else:
            # do pid checking
            log.warning('Process is locked. Another instance is running.')
            if retry != 0:
                for each in range(retry):
                    time.sleep(5)
                    if aquireLock():
                        self.lock_handle.write(self.ppid)
                        self.lock_handle.close()
                        atexit.register(self.unlock)
                        return True

        log.error('Could not obtain process lock. Exiting')
        exit(1)

    def unlock(self):
        try:
            fcntl.flock(self.lock_handle, fcntl.LOCK_UN)
            self.lock_handle.close()
        except:
            pass
        if os.path.isfile(self.lockfile):
            os.remove(self.lockfile)
