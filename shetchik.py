# Program for elektroschetchik Energomera CE307 USB/RS232/COM/Serial to RS485. Программа подключается к локальному MQTT брокеру и публикует сообщения для AutoDiscovery для Home Assistant. 
# Didenko Alexandr vk.com/Bagunda. https://github.com/Bagunda/energomera_ce307
# Для Linux на основе OpenWRT (в моём случае это Onion Omega2p):
# opkg install python3-light
# pip3 install paho-mqtt
# pip3 install pyserial
# pip3 install requests

import serial
from subprocess import call
import time
import os
import subprocess
import signal
import datetime as DT

import paho.mqtt.client as mqtt
import json

SCHETCHIK_MANUFACTURE = "Energomera" # Для MQTT
SCHETCHIK_MODEL = "CE307" # Для MQTT
SCHETCHIK_SERIAL_NUMBER = "011791165813462" # Для MQTT
SCHETCHIK_UNIQ_ID = "energy_counter_" + SCHETCHIK_SERIAL_NUMBER # Для MQTT

ProgrammName = "schetchik"
def tologread(msg):
    call(["logger", "-t", ProgrammName, msg])
    # print(msg)

now = DT.datetime.now(DT.timezone.utc).astimezone()
time_format = "%Y-%m-%d %H:%M:%S"
tologread("Program runing...")

pl = subprocess.Popen(['ps'], stdout=subprocess.PIPE).communicate()[0]
string_ps = pl.decode("utf-8")
pids = []

for line in string_ps.splitlines():
    if 'schetchik.py' in line:
        pids.append(int(line.split(None, 1)[0]))

pids.pop(-1)

for pid in pids:
    os.kill(int(pid), signal.SIGINT)
    tologread("Killed previously runned schetchik.py pid=" + str(pid))

    
COM_PortName = "/dev/ttyUSB0"
COM_Port = serial.Serial(COM_PortName) # open the COM port

COM_Port.baudrate = 9600               # set Baud rate 
COM_Port.bytesize = 8                  # Number of data bits = 8
COM_Port.parity   = 'N'                # No parity
COM_Port.stopbits = 1                  # Number of Stop bits = 1

# print('\n    Baud rate = ',COM_Port.baudrate)
# print('    Data bits = ',COM_Port.bytesize)
# print('    Parity    = ',COM_Port.parity)
# print('    Stop bits = ',COM_Port.stopbits)
# print('\n    Waiting for data.....\n')

def RequestTarif(num):
    # 0 - summ
    # 1 - tarif 1
    # 2 - tarif 2
    # 3 - tarif 3
    time.sleep(1)
    if num == 0:
        values = bytearray([0xC0, 0x48, 0x96, 0x34, 0xFD, 0x00, 0x00, 0x00, 0x00, 0x00, 0xD2, 0x01, 0x30, 0x00, 0x00, 0x40, 0xC0])
    elif num == 1:
        values = bytearray([0xC0, 0x48, 0x96, 0x34, 0xFD, 0x00, 0x00, 0x00, 0x00, 0x00, 0xD2, 0x01, 0x30, 0x00, 0x01, 0xF5, 0xC0])
    elif num == 2:
        values = bytearray([0xC0, 0x48, 0x96, 0x34, 0xFD, 0x00, 0x00, 0x00, 0x00, 0x00, 0xD2, 0x01, 0x30, 0x00, 0x02, 0x9F, 0xC0])
    elif num == 3:
        values = bytearray([0xC0, 0x48, 0x96, 0x34, 0xFD, 0x00, 0x00, 0x00, 0x00, 0x00, 0xD2, 0x01, 0x30, 0x00, 0x03, 0x2A, 0xC0])
    COM_Port.write(values)

RequestTarif(0)

count = 1

st1 = time.time()
arr = []
arr_hex_str = []

kw_summ_geted = False
kw_tarif1_geted = False
kw_tarif2_geted = False
kw_tarif3_geted = False
first_count_done = False
cycle_work = True


my_file = open("device_id") # В тойже папке, где лежит программа должен быть файл с именем "device_id", в котором записываем примерно такое "LinuxOpenWRT_v_electroschitke". У меня этот device_id используется и в других программах на этой машине
device_id = my_file.read()
my_file.close()

my_file = open("/root/mqtt_credentials.json") # В тойже папке, где лежит программа должен быть файл с именем "mqtt_credentials.json", в котором записываем такое: {"localmashine": {"host": "127.0.0.1", "port": "1883", "user": "MQTTuser", "password": "MQTTpass"}}
my_string = my_file.read()
my_file.close()
mqtt_credentials_from_file_dict = json.loads(my_string)

MQTTtopic_header = "KP"
MQTT_client_id_publisher = device_id + '_publisher_in_listener'
MQTT_client_id_subscriber = device_id + '_listener'



class MyMQTTClass(mqtt.Client):
    rc_txt = {
        0: "Connection successful",
        1: "Connection refused - incorrect protocol version",
        2: "Connection refused - invalid client identifier",
        3: "Connection refused - server unavailable",
        4: "Connection refused - bad username or password",
        5: "Connection refused - not authorised"
    }

    def setPlaces(self, name, host, port, user, password, topic_header, subscribe_to_topic):
        self.BRname = name
        self.BRhost = str(host)
        self.BRport = int(port)
        self.BRuser = str(user)
        self.BRpassword = str(password)
        self.BRclient_id = str(self._client_id)
        self.BRtopic_header = str(topic_header)
        self.subscribe_to_topic = subscribe_to_topic
        self.connected_flag = False

    def BRinfo(self):
        tologread ("Connection data: {} ({}:{}), u={}, pass={}, client_id={}, topic_header={}, topic={}".format(self.BRname, self.BRhost, self.BRport, self.BRuser, self.BRpassword, self.BRclient_id, self.BRtopic_header, self.subscribe_to_topic))
        pass

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            self.connected_flag = False
            msg="Unexpected disconnection"
            tologread(msg)

    def on_connect(self, mqttc, obj, flags, rc):
        if rc == 0:
            tologread("Brocker=" + self.BRname + ", rc: " + str(rc) + " (" + self.rc_txt[rc] + ")")
            self.connected_flag=True

            topicall = self.BRtopic_header + self.subscribe_to_topic
            res = self.subscribe(topicall)
            if rc == mqtt.MQTT_ERR_SUCCESS:
                tologread("Successfully subscribed to topic: " + topicall)
                self.publish(self.BRtopic_header, "online", qos=0, retain=True)
            else:
                msg="Error! Client is not subscribed to topic " + topicall
                tologread(msg)
        else:
            self.connected_flag = False
            msg="Unexpected disconnection"
            tologread(msg)


    def on_message(self, mqttc, obj, msg):
        print("Brocker=" + self.BRname + ". Recieved msg: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        tologread("Brocker=" + self.BRname + ", topic=" + self.BRtopic_header + self.subscribe_to_topic + ", subscribed: mid=" + str(mid) + ", granted_qos=" + str(granted_qos))

    def on_log(self, mqttc, obj, level, string):
        pass

    def bag_pub(self, topic, payload):
        if (self.connected_flag == True):
            topic2 = self.BRtopic_header + topic

            (rc, mid) = self.publish(topic2, payload)
            if (rc != 0):
                self.connected_flag = False
                msg="Error to send mqtt. rc=" + str(rc) + ". " + str(self.rc_txt[rc]) + ". mid=" + str(mid)
                tologread(msg)
            else:
                tologread ("Success send mqtt: {}, t={}, msg={}".format(self.BRname, topic2, payload))
        else:
            tologread ("Scipped trying send mqtt because connected_flag = False")

    def run2(self):
        self.username_pw_set(username=self.BRuser,password=self.BRpassword)

        try:
            tologread(self.BRtopic_header)
            self.will_set(self.BRtopic_header, 'offline', 0, False)
            self.connect(self.BRhost, self.BRport, 60)
        except Exception as error_string:
            msg="Error to connect mqtt. Broker={}. Error: {}".format(self.BRname, str(error_string))
            tologread(msg)
            pass

        self.loop_start()

    def exit(self):
        self.disconnect()
        self.loop_stop()


class Localnet_on_message(MyMQTTClass):
    def on_message(self, mqttc, obj, msg):
        tologread("Recieved msg: {}, topic={}, brocker={}".format(str(msg.payload), msg.topic, self.BRname))

MQTTtopic_header = "homeassistant/sensor/ElectroSchetchik"

localnet = Localnet_on_message(client_id=device_id + "_" + ProgrammName)
localnet.setPlaces(
    name="localnet",
    host=mqtt_credentials_from_file_dict.get("localmashine").get("host"),
    port=int(mqtt_credentials_from_file_dict.get("localmashine").get("port")),
    user=mqtt_credentials_from_file_dict.get("localmashine").get("user"),
    password=mqtt_credentials_from_file_dict.get("localmashine").get("password"),
    topic_header=MQTTtopic_header,
    subscribe_to_topic = "command/#")
localnet.BRinfo()
localnet.run2()

while localnet.connected_flag == False:
    pass

device_dict = {"identifiers": [SCHETCHIK_UNIQ_ID], "mf": "Omega2p", "mdl": SCHETCHIK_MANUFACTURE + " " + SCHETCHIK_MODEL, "sw": "1.0", "name": "Электросчётчик " + SCHETCHIK_MANUFACTURE + " " + SCHETCHIK_MODEL + " " + SCHETCHIK_SERIAL_NUMBER }

Sum_dict = {
    'name': 'Сумма T1+T2+T3',
    'device_class': "energy",
    "object_id": SCHETCHIK_UNIQ_ID + "_sum",
    "state_topic": "homeassistant/sensor/ElectroSchetchik/state",
    "unit_of_measurement": "kWh",
    "value_template": "{{ value_json.sum}}",
    "unique_id": SCHETCHIK_UNIQ_ID + "_sum",
    "state_class": "total_increasing",
    "device": device_dict
}
Sum_json = json.dumps(Sum_dict)
localnet.bag_pub("/config", Sum_json)

time.sleep(1)

T1_dict = {
    'name': 'Тариф T1',
    'device_class': "energy",
    "object_id": SCHETCHIK_UNIQ_ID + "_t1",
    "state_topic": "homeassistant/sensor/ElectroSchetchik/state",
    "unit_of_measurement": "kWh",
    "value_template": "{{ value_json.t1}}",
    "unique_id": SCHETCHIK_UNIQ_ID + "_t1",
    "state_class": "total_increasing",
    "device": device_dict
}
T1_json = json.dumps(T1_dict)
localnet.bag_pub("/t1/config", T1_json)

time.sleep(1)

T2_dict = {
    'name': 'Тариф T2',
    'device_class': "energy",
    "object_id": SCHETCHIK_UNIQ_ID + "_t2",
    "state_topic": "homeassistant/sensor/ElectroSchetchik/state",
    "unit_of_measurement": "kWh",
    "value_template": "{{ value_json.t2}}",
    "unique_id": SCHETCHIK_UNIQ_ID + "_t2",
    "state_class": "total_increasing",
    "device": device_dict
}
T2_json = json.dumps(T2_dict)
localnet.bag_pub("/t2/config", T2_json)

time.sleep(1)

T3_dict = {
    'name': 'Тариф T3',
    'device_class': "energy",
    "object_id": SCHETCHIK_UNIQ_ID + "_t3",
    "state_topic": "homeassistant/sensor/ElectroSchetchik/state",
    "unit_of_measurement": "kWh",
    "value_template": "{{ value_json.t3}}",
    "unique_id": SCHETCHIK_UNIQ_ID + "_t3",
    "state_class": "total_increasing",
    "device": device_dict
}
T3_json = json.dumps(T3_dict)
localnet.bag_pub("/t3/config", T3_json)

while cycle_work:
    for line in COM_Port.read():
        dd = "{:02x}".format(line)
        ddd = chr(line)

        count = count+1
        if (time.time() - st1 > 1):
            st1=time.time()
            if (line == 0xC0):
                arr = []
                arr_hex_str = []

            if kw_summ_geted == True and kw_tarif1_geted == True and kw_tarif2_geted == True and kw_tarif3_geted == True:
                kw_summ_geted = False
                kw_tarif1_geted = False
                kw_tarif2_geted = False
                kw_tarif3_geted = False
                first_count_done = False

        else:
            if (line == 0xC0):
                if len(arr) == 16:
                    if (arr[0] == 0x48 and arr[1] == 0xFD and arr[2] == 0x00 and arr[3] == 0x96 and arr[4] == 0x34 and arr[5] == 0x57 and arr[6] == 0x01 and arr[7] == 0x30):
                        if kw_summ_geted == False and kw_tarif1_geted == False:
                            kw_summ0 = int((arr[14] << 24) + (arr[13] << 16) + (arr[12] << 8) + arr[11])
                            kw_summ =  '{0:.2f}\n'.format(kw_summ0 / 100)
                            
                            if first_count_done == False:
                                kw_summ_last = kw_summ
                                
                                RequestTarif(0)
                                first_count_done = True
                            else:
                                if kw_summ == kw_summ_last:
                                    kw_summ_checked = kw_summ.strip()
                                    kw_summ_geted = True
                                    first_count_done = False
                                    tologread ("PACKET ELEKTRO SUMM CHECKED: " + str(kw_summ_checked))
                            
                                    payload = kw_summ_checked
                                    localnet.bag_pub("/state", '{ "sum": ' + str(payload) + '}')

                                    RequestTarif(1)
                                    continue

                        if kw_summ_geted == True and kw_tarif1_geted == False:
                            kw_tarif1_0 = int((arr[14] << 24) + (arr[13] << 16) + (arr[12] << 8) + arr[11])
                            kw_tarif1 =  '{0:.2f}\n'.format(kw_tarif1_0 / 100)
                            
                            if first_count_done == False:
                                kw_tarif1_last = kw_tarif1
                                
                                RequestTarif(1)
                                first_count_done = True
                            else:
                                if kw_tarif1 == kw_tarif1_last:
                                    kw_tarif1_checked = kw_tarif1.strip()
                                    kw_tarif1_geted = True
                                    first_count_done = False
                                    tologread ("PACKET ELEKTRO TARIF1 CHECKED: " + str(kw_tarif1_checked))
                            
                                    payload = kw_tarif1_checked
                                    localnet.bag_pub("/state", '{ "t1": ' + str(payload) + '}')

                                    RequestTarif(2)
                                    continue

                        if kw_summ_geted == True and kw_tarif1_geted == True and kw_tarif2_geted == False:
                            kw_tarif2_0 = int((arr[14] << 24) + (arr[13] << 16) + (arr[12] << 8) + arr[11])
                            kw_tarif2 =  '{0:.2f}\n'.format(kw_tarif2_0 / 100)
                            
                            if first_count_done == False:
                                kw_tarif2_last = kw_tarif2
                                
                                RequestTarif(2)
                                first_count_done = True
                            else:
                                if kw_tarif2 == kw_tarif2_last:
                                    kw_tarif2_checked = kw_tarif2.strip()
                                    kw_tarif2_geted = True
                                    first_count_done = False
                                    tologread ("PACKET ELEKTRO TARIF2 CHECKED: " + str(kw_tarif2_checked))
                            
                                    payload = kw_tarif2_checked
                                    localnet.bag_pub("/state", '{ "t2": ' + str(payload) + '}')
                            
                                    RequestTarif(3)
                                    continue

                        if kw_summ_geted == True and kw_tarif1_geted == True and kw_tarif2_geted == True and kw_tarif3_geted == False:
                            kw_tarif3_0 = int((arr[14] << 24) + (arr[13] << 16) + (arr[12] << 8) + arr[11])
                            kw_tarif3 =  '{0:.2f}\n'.format(kw_tarif3_0 / 100)
                            
                            if first_count_done == False:
                                kw_tarif3_last = kw_tarif3
                                
                                RequestTarif(3)
                                first_count_done = True
                            else:
                                if kw_tarif3 == kw_tarif3_last:
                                    kw_tarif3_checked = kw_tarif3.strip()
                                    kw_tarif3_geted = True
                                    first_count_done = False
                                    tologread ("PACKET ELEKTRO TARIF3 CHECKED: " + str(kw_tarif3_checked))
                            
                                    payload = kw_tarif3_checked
                                    localnet.bag_pub("/state", '{ "t3": ' + str(payload) + '}')

                                    cycle_work = False
                                    break
                                    continue
                    else:
                        tologread ("GOT C0, packet lenght 16, but not needed answer")
                else:
                    tologread ("GOT C0, but packet lenght not 16")
            else:
                arr.append(line)
                arr_hex_str.append(dd)
