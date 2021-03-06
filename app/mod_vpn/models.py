import os
from app import app
from re import search
import ipgetter
import subprocess
import signal
from werkzeug.utils import secure_filename


VPN_FOLDER = app.config["BASE_DIR"] + "/openvpn/"


def parse_ip(conf):
    ip = None
    if os.path.exists(conf):
        f = open(conf, "r")
        content = f.read()
        try:
            re_ip = search(r'remote(.+?)1194', content)
            ip = str(re_ip.group(1)).strip()
        except Exception, e:
            print e
            ip = None
    return ip


class VPN(object):

    def __init__(self):
        self.vpns = dict()
        self.vpn_client_pid = None
        self.vpn_connected = None

    def connect(self, vpn):
        self.disconnect()
        vpn = secure_filename(vpn)
        response = {"message": None, "pid": None, "status": False, "name": vpn, "last": self.vpn_connected}

        if vpn == "":
            response["message"] = "vpn is empty!"
            return response
        path_vpn = VPN_FOLDER + vpn + "/"
        command = "/usr/bin/nohup /usr/sbin/openvpn --cd " + path_vpn + " --config client.ovpn >/dev/null 2>&1 & /bin/echo $!"
        if os.path.exists(path_vpn):
            if os.path.exists("/usr/bin/nohup") and os.path.exists("/usr/sbin/openvpn"):
                proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                self.vpn_client_pid = int(proc.communicate()[0].strip())
                response["message"] = "Connected to VPN Server"
                response["pid"] = self.vpn_client_pid
                response["status"] = True
                self.vpn_connected = vpn
            else:
                response["message"] = "nohup or openvpn is not found!"
        return response

    def disconnect(self):
        try:
            if self.vpn_client_pid:
                os.kill(self.vpn_client_pid, signal.SIGTERM)
        except OSError:
            return False
        else:
            return True

    def status(self):
        pid_path = "/proc/%s" % self.vpn_client_pid
        if os.path.exists(pid_path):
            return True
        return False

    def get_list(self):
        vpn_configs = os.listdir(VPN_FOLDER)
        for vpn in vpn_configs:
            _vpn = {"conf": None,
                    "ip": None,
                    "status": False,
                    "name": None}
            vpn_path = VPN_FOLDER + vpn
            if os.path.isdir(vpn_path):
                conf = vpn_path + "/" + "client.ovpn"
                _vpn["conf"] = conf
                _vpn["ip"] = parse_ip(conf)
                _vpn["name"] = vpn
                if vpn == self.vpn_connected:
                    _vpn["status"] = True
                self.vpns[vpn] = _vpn
        return self.vpns

    def external_ip(self):
        ip = ipgetter.myip()
        return ip