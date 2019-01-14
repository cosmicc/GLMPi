import subprocess
from time import sleep

if __name__ == '__main__':
        p = subprocess.Popen("arp-scan -l", stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        p_status = p.wait()
        output = output.decode('UTF-8').split('\n')
        #print(output)
        for each in output:
            line = (each.split('\t'))
            if len(line) > 2:
                print(line[1])
