from configparser import ConfigParser
from time import sleep
from datetime import datetime
from loguru import logger as log
import csv
import os
from threads.threadqueues import alarm_queue, restapi_queue
from modules.extras import End


class alarmHandler():
    def __init__(self):
        config = ConfigParser()
        config.read('/etc/glmpi.conf')
        self.alarmfile = config.get('general', 'alarms')
        if os.path.isfile(self.alarmfile):
            self.alarms = []
            self.read_alarmfile()
        else:
            self.create_alarmfile()
            self.alarms = []
            self.alarmcount = 0

    def create_alarmfile(self):
        os.system(f'touch {self.alarmfile}')
        log.debug(f'New Alarm save file created: {self.alarmfile}')
#        header = ['timestamp', 'alarm']
#        with open(self.alarmfile, mode='w') as a_file:
#            alarm_writer = csv.writer(a_file, fieldnames=header, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
#            alarm_writer.writeheader(header)

    def insert_alarm(self, alarm):
            dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            Row = [str(dt), f"{alarm[0]}"]
            self.alarms.append(Row)
            self.alarmcount += 1
            with open(self.alarmfile, mode='a') as a_file:
                alarm_writer = csv.writer(a_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                alarm_writer.writerow(Row)
            log.debug(f'New Alarm has been inserted: {Row}')

    def read_alarmfile(self):
        with open(self.alarmfile) as alarm_file:
            alarm_reader = csv.reader(alarm_file, delimiter=',')
            line_count = 0
            for row in alarm_reader:
                self.alarms.append([row[0], row[1]])
                line_count += 1
            self.alarmcount = line_count
            log.debug(f'Found {line_count} saved alarms from alarmfile')

    def reset_alarms(self):
        if os.path.isfile(self.alarmfile):
            self.alarmcount = 0
            self.alarms = []
            os.remove(self.alarmfile)
            self.create_alarmfile()
            log.info('Alarms have been reset')
        else:
            log.warning('Alarm reset, but no alarms file was found. creating')
            self.create_alarmfile()


def alarms_thread():
    log.info('Alarm handler thread is starting')
    alarms = alarmHandler()
    while True:
        try:
            if not alarm_queue.empty():
                alarmqueue = alarm_queue.get()
                if alarmqueue[0] == 'getalarms':
                    restapi_queue.put({alarms.alarmcount: alarms.alarms})
                elif alarmqueue[0] == 'alarmsreset':
                    alarms.reset_alarms()
                    restapi_queue.put('SUCCESS')
                else:
                    if len(alarms.alarms) > 0:
                        lastalarm = alarms.alarms[-1]
                        log.warning(f'LAST ALARM: {lastalarm} - THIS ALARM: {alarmqueue[0]}')
                        if lastalarm[1] != alarmqueue[0]:
                            alarms.insert_alarm(alarmqueue)
                        else:
                            log.debug(f'Skipping duplicate alarm entry: {alarmqueue}')
                    else:
                        alarms.insert_alarm(alarmqueue)

            sleep(.5)
        except:
            log.critical(f'Exception in Error Handler Thread', exc_info=True)
            End('Exception in Error Handler Thread')
    End('Error Handler thread loop ended prematurely')
