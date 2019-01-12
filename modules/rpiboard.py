from os import uname, getenv, popen
from socket import gethostname
from subprocess import check_output, Popen, PIPE
from modules.extras import float_trunc_1dec

def is_root():
    if getenv("SUDO_USER") == None:
        return False
    else:
        return True

def is_rpi():
    funame = uname()
    if funame[4][:3] == 'arm':
        return True
    else:
        return False

def is_zero():
    if 'Zero' in rpi_board():
        return True
    else:
        return False

def rpi_mem():
    memory = {}
    armmem = check_output(['/usr/bin/vcgencmd', 'get_mem', 'arm'], shell=False)
    gpumem = check_output(['/usr/bin/vcgencmd', 'get_mem', 'gpu'], shell=False)
    memory.update({'system':armmem, 'gpu':gpumem})
    return memory

def rpi_board():
    try:
        file = open('/sys/firmware/devicetree/base/model', 'r')
        model = file.read()
        file.close()
    except:
        return None
    else:
        return model.rstrip('\x00')

def enable_hdmi():
    try:
        check_output(['/usr/bin/tvservice', '-p'], shell=False)
    except:
        return False
    else:
        return True

def disable_hdmi():
    try:
        check_output(['/usr/bin/tvservice', '-o'], shell=False)
    except:
        return False
    else:
        return True

def get_freemem():
    fm = Popen(['/usr/bin/free', '-h'], stdout=PIPE)
    i = 0
    freemem = {}
    while True:
        i += 1
        line = str(fm.stdout.readline())
        if i == 2:
            line = line.split()
            freemem.update({'total':line[1], 'used':line[2], 'free':line[3], 'available':line[6].strip("\\n'")})
        if i == 3:
            line = line.split()
            freemem.update({'swap':line[2]})
            return freemem

def get_diskspace():
    ds = Popen(['/bin/df', '-h', '/'], stdout=PIPE)
    i = 0
    diskspace = {}
    while True:
        i += 1
        line = str(ds.stdout.readline())
        if i == 2:
            line = line.split()
            diskspace.update({'size':line[1], 'available':line[3], 'used':line[2], 'used_percent':line[4]})
            return diskspace

def rpi_info():
    rpiinfo = {}
    runame = uname()
    cores = 0
    rpiinfo.update({'hostname':gethostname(), 'system':runame[0], 'release':runame[2], 'version':runame[3], 'machine':runame[4], 'board':rpi_board()})
    cpuinfofile = open('/proc/cpuinfo')
    for line in cpuinfofile:
        line = line.split(':')
        if line[0].startswith('Serial'):
            rpiinfo.update({'serial':line[1].strip('\n').strip()})
        elif line[0].startswith('Hardware'):
            rpiinfo.update({'hardware':line[1].strip('\n').strip()})
        elif line[0].startswith('processor'):
            cores += 1
        elif line[0].startswith('Revision'):
            rpiinfo.update({'revision':line[1].strip('\n').strip()})
        elif line[0].startswith('model name'):
            rpiinfo.update({'cpu_model':line[1].strip('\n').strip()})
    cpuinfofile.close()
    rpiinfo.update({'cores':cores})
    return rpiinfo

class Led(object):
    def __init__(self, ledtype):
        self.ledtype = ledtype
        if is_zero():
            self.fon = '0'
            self.foff = '1'
        else:
            self.fon = '1'
            self.foff = '0'
        if self.ledtype == 'status' or self.ledtype == 'st':
            self.led = 'led0'
        elif self.ledtype == 'power' or self.ledtype == 'pwd':
            self.led = 'led1'
        else:
            raise NameError('Invalid onboard LED specified')
        #if not is_root():
        #    raise RuntimeError("Controlling onboard LED's requires ROOT")
        trig = open('/sys/class/leds/{}/trigger'.format(self.led), 'w')
        trig.write('none')
        trig.close()
        check_output(['modprobe', 'ledtrig_heartbeat'], shell=False)

    def ledon(self):
        lo = open('/sys/class/leds/{}/brightness'.format(self.led), 'w')
        lo.write(self.fon)
        lo.close()

    def ledoff(self):
        noop = open('/sys/class/leds/{}/trigger'.format(self.led), 'w')
        noop.write('none')
        noop.close()
        loff = open('/sys/class/leds/{}/brightness'.format(self.led), 'w')
        loff.write(self.foff)
        loff.close()

    def ledflash(self):
        fla = open('/sys/class/leds/{}/trigger'.format(self.led), 'w')
        fla.write('heartbeat')
        fla.close()

def cpu_temp():
    tempu = popen("vcgencmd measure_temp").readline()
    tempu = tempu.replace("temp=","")
    tempu = tempu.replace("'C","")
    return float_trunc_1dec(float(tempu))

def system_uptime():
    ut = check_output(['uptime', '-p'], shell=False).decode("utf-8").strip()
    ur = ut.split('up ')
    return ur[1]
