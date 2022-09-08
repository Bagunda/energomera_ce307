# Program for elektroschetchik Energomera CE307 USB/RS232/COM/Serial to RS485
# Didenko Alexandr vk.com/Bagunda. https://github.com/Bagunda/energomera_ce307

import serial
import time
import requests

COM_PortName = "/dev/ttyUSB0"
COM_Port = serial.Serial(COM_PortName) # open the COM port
print('\n   ',COM_PortName,'Opened')

COM_Port.baudrate = 9600               # set Baud rate 
COM_Port.bytesize = 8                  # Number of data bits = 8
COM_Port.parity   = 'N'                # No parity
COM_Port.stopbits = 1                  # Number of Stop bits = 1

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
                                    kw_summ_checked = kw_summ
                                    kw_summ_geted = True
                                    first_count_done = False
                                    print ("PACKET ELEKTRO SUMM CHECKED: " + str(kw_summ_checked))
                            
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
                                    kw_tarif1_checked = kw_tarif1
                                    kw_tarif1_geted = True
                                    first_count_done = False
                                    print ("PACKET ELEKTRO TARIF1 CHECKED: " + str(kw_tarif1_checked))
                            
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
                                    kw_tarif2_checked = kw_tarif2
                                    kw_tarif2_geted = True
                                    first_count_done = False
                                    print ("PACKET ELEKTRO TARIF2 CHECKED: " + str(kw_tarif2_checked))
                            
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
                                    kw_tarif3_checked = kw_tarif3
                                    kw_tarif3_geted = True
                                    first_count_done = False
                                    print ("PACKET ELEKTRO TARIF3 CHECKED: " + str(kw_tarif3_checked))

                                    dict_for_json = {"summ": kw_summ_checked, "tarif1": kw_tarif1_checked, "tarif2": kw_tarif2_checked, "tarif3": kw_tarif3_checked}
                                    r = requests.post('http://10.11.12.10:8123/api/webhook/webhook_from_schetchik', json=dict_for_json)
                                    print(r.status_code)

                                    cycle_work = False
                                    break
                                    continue

            else:
                arr.append(line)
                arr_hex_str.append(dd)

