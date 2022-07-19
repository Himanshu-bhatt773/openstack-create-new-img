#!/usr/bin/env python
import os, sys
import subprocess, json, time, winrm
from pathlib import Path
import pathlib
import re
class colors:
    reset='\033[0m'
    bold='\033[01m'
    disable='\033[02m'
    underline='\033[04m'
    reverse='\033[07m'
    strikethrough='\033[09m'
    invisible='\033[08m'
    class fg:
        black='\033[30m'
        red='\033[31m'
        green='\033[32m'
        orange='\033[33m'
        blue='\033[34m'
        purple='\033[35m'
        cyan='\033[36m'
        lightgrey='\033[37m'
        darkgrey='\033[90m'
        lightred='\033[91m'
        lightgreen='\033[92m'
        yellow='\033[93m'
        lightblue='\033[94m'
        pink='\033[95m'
        lightcyan='\033[96m'

#########3#### Playground VPC environment variables, use this for instance creation###########
my_play = os.environ.copy()
my_play["OS_AUTH_URL"]= "https://rfx.cloudlocity.net:5000"
my_play["OS_PROJECT_ID"]= "c41fdba5a93742f5a8daaa3495f39017"
my_play["OS_PROJECT_NAME"]= "main"
my_play["OS_USER_DOMAIN_NAME"]= "playground"
my_play["OS_PROJECT_DOMAIN_ID"]= "d697d091d4bf42e890adea5901a4c437"
my_play["OS_USERNAME"]= "domain-admin"
my_play["OS_PASSWORD"]= "$#X%3O7a(]-CA7i3*"
my_play["OS_REGION_NAME"]= "RegionOne"
my_play["OS_INTERFACE"]= "public"
my_play["OS_IDENTITY_API_VERSION"]= "3"

####Admin VPC environment variables, use this for other operations since admin has access to all #############
my_admin = os.environ.copy()
my_admin["OS_PROJECT_DOMAIN_NAME"]= "default"
my_admin["OS_USER_DOMAIN_NAME"]= "default"
my_admin["OS_PROJECT_NAME"]= "admin"
my_admin["OS_USERNAME"]= "admin"
my_admin["OS_PASSWORD"]= "80aff0aa18796f4930dc5a65f6a9b0d372732ccaaa67b1670c382f8b8"
my_admin["OS_AUTH_URL"]= "https://rfx.cloudlocity.net:5000"
my_admin["OS_IDENTITY_API_VERSION"]= "3"
my_admin["OS_IMAGE_API_VERSION"]= "2"
my_admin["OS_SHARE_API_VERSION"]= "2.51"
my_admin["OS_PLACEMENT_API_VERSION"]= "1.10"
my_admin["OS_COMPUTE_API_VERSION"]= "2.55"



#Variable Definition written here
instance_uuid = "e55f32ad-8d90-4835-904d-6e31f184357f"
play_key_name = "key-pair-01"
play_netid = "a22b5b5e-5d76-47f1-940b-e1b6f24adc73"

##############Function for passing commands to shell ####################
def call_bshell(bscmd,my_env):
    p = subprocess.Popen([bscmd], env=my_env, shell=True, stdout=subprocess.PIPE)
    o = p.communicate()[0].decode("utf-8")
    return o

############################Script to create image from a running instance.
print (colors.fg.blue,'\n This script targets creating a new image from an existing instance on RFX cloud',colors.reset)

####################Fetch instance details from the cloud.
print (colors.fg.blue,'\n Fetching instance details from the openstack environment',colors.reset)

output1 = call_bshell(("openstack server show {} -f json".format(instance_uuid)),my_admin)
joutput1 = json.loads(output1)

print (colors.fg.blue,"\nThe openstack instance details are as follows \n",colors.fg.green,joutput1,colors.reset)

####################shelve instance to create image ###########
print (colors.fg.blue,'\n Shelving the instance to create shelved image',colors.reset)
if (joutput1['status'] == "ACTIVE"):   
     p2 = call_bshell(("openstack server shelve {}".format(instance_uuid)),my_admin)
else:
    print (colors.fg.red,"Instance state is not ACTIVE, not proceeding, Aborted !!!",colors.reset)
    exit()

shelved_img_name = joutput1['name']+"-shelved"
print (colors.fg.blue,"\n Instance shelved image name is: ",colors.fg.green,shelved_img_name,colors.reset)

###################Check if shelved image is available for use #############
imgstatus = "NA"
while (imgstatus != "active"):
    time.sleep(30)
    p3 = call_bshell(("openstack image show {} -f json".format(shelved_img_name)),my_admin)
    joutput3 = json.loads(p3)
    if (joutput3['status'] == "active"):
        print (colors.fg.yellow,"\n The shelved image {} is now available for further operations".format(shelved_img_name),colors.reset)
        imgstatus = joutput3['status']
    print (colors.fg.pink,"\n The shelved image {} is now {}".format(shelved_img_name, joutput3['status']),colors.reset)

##################Create new instance with this new image ##################

output4 = call_bshell(("openstack server create --flavor m.xlarge --image {} --key-name {} --security-group winrm_rdp --network {} shelve_ins -f json".format(shelved_img_name,play_key_name,play_netid)),my_play) 
joutput4 = json.loads(output4)
print ("\n Creating instance with new image: ",joutput4)

########################## check new instance is active or not for futher operations ######################
newinst_uuid = joutput4['id']

insstatus = "NA"
while (insstatus != "ACTIVE"):
    time.sleep(30)
    p5 = call_bshell(("openstack server  show {} -f json".format(newinst_uuid)),my_play)
    joutput5 = json.loads(p5)
    if (joutput5['status'] == "ACTIVE"):
        print (colors.fg.blue,"\n The Instance  {} is now available for further operations".format(newinst_uuid),colors.reset)
        insstatus = joutput5['status']
    print (colors.fg.pink,"\n The instance  {} is now {}".format(newinst_uuid, joutput5['status']),colors.reset)

print (colors.fg.green,"\nThe openstack instance details are as follows ",colors.fg.green,joutput5,colors.reset)

###########################3# assign floating IP on new instance ###############################################################

output6 = call_bshell(("openstack floating ip create RFX_public -f json"),my_play)
joutput6 = json.loads(output6)
floating_ip = joutput6['floating_ip_address']
print (colors.fg.blue,"\n floating IP   \n",floating_ip,colors.reset)
output7 = call_bshell(("openstack server add floating ip {} {}".format(newinst_uuid,floating_ip)),my_play)
print (colors.fg.blue,"\n floating IP is added \n",output7,colors.reset)

#################### Once server status becomes active. Check if key present on the instance exists locally, if so retrieve instance password##################
print (colors.fg.blue,'\nChecking if the ssh key required exists locally',colors.reset)
inst_key = pathlib.Path('key-pair-01.pem')
time.sleep(350)
if inst_key.exists():
    print (colors.fg.blue,"\nSSH Keypair Exists, Proceeding to extract instance password",colors.reset)
    p8 = call_bshell(("nova get-password {} {}".format(newinst_uuid,inst_key)),my_play)
    print (colors.fg.blue,"\nInstance password is: \t",p8,colors.reset)
else:
    print (colors.fg.red,"\nUnable to find ssh key locally, Exitting !!!!",colors.reset)
    exit()

######################### connect to instance through winrm  ###############################################################
password= p8
password = password.strip()
length = len(password)
ip = joutput6['floating_ip_address']
session = winrm.Session(ip, auth=(user,password))

################################################ uninstall Cloudbase init ####################################################

out = session.run_ps("$MyApp = Get-WmiObject -Class Win32_Product | Where-Object{$_.Name -eq 'Cloudbase-Init 1.1.2'} \n $MyApp.Uninstall()")
print(colors.fg.blue,"\n uninstall cloudbaseinit:\t",out.std_out,colors.reset)

################shrink disk to maximun ###################

out1 = session.run_ps("(Get-PartitionSupportedSize -DriveLetter C).SizeMin")
min_size_poss =  int(out1.std_out.decode("utf-8"))
extra = 10*1024*1024*1024
min_size_poss = int(min_size_poss) + int(extra)
print(colors.fg.blue,"\n Minimum size possible for the partition is ",colors.fg.green,min_size_poss,colors.reset)
currentsize = session.run_ps("(Get-Partition -DriveLetter C).Size")
currentsize = int(currentsize.std_out.decode("utf-8"))
print(colors.fg.blue,"\n Current Size of the partition is ",colors.fg.green,currentsize,colors.reset)

if currentsize > min_size_poss:
    out2 = session.run_ps("Resize-Partition -DriveLetter C -Size {}".format(min_size_poss))
    out3 = session.run_ps("(Get-Partition -DriveLetter C).Size")
    print (colors.fg.blue,"\n Partition shrinked to maximum possible value ",colors.fg.green,out3.std_out,colors.reset)
else:
    print (colors.fg.red,"\n Already Shrinked",colors.reset)

############################install cloudbase init ##############################

out4 = session.run_ps('Invoke-WebRequest -Uri http://107.155.99.62/CloudbaseInitSetup_1_1_2_x64 -UseBasicParsing -OutFile C:\\Users\\Admin\\Downloads\\CloudbaseInitSetup_1_1_2_x64')
print(colors.fg.blue,"\n Cloudinit Download Complete",colors.fg.green,out4.std_out,colors.reset)
out5 = session.run_ps("Start-Process msiexec.exe -ArgumentList '/i C:\\Users\\Admin\Downloads\\CloudbaseInitSetup_1_1_2_x64  /qn /norestart RUN_SERVICE_AS_LOCAL_SYSTEM=1' -Wait")
print(colors.fg.blue,"\n Installation Completed",colors.fg.green,out5.std_out,colors.reset)
out6 = session.run_ps('Start-Sleep -Seconds 120')
out7 = session.run_ps('Invoke-WebRequest -Uri http://107.155.99.62/cloudbase-init-unattend.conf -UseBasicParsing -OutFile C:\\Users\\Admin\\Downloads\\cloudbase-init-unattend.conf')
print(colors.fg.blue,"\n Installation Completed",colors.fg.green,out7.std_out,colors.reset)
out8 = session.run_ps('Copy-Item -Path "C:\\Users\\Admin\\Downloads\\cloudbase-init-unattend.conf"  -Destination "C:\\Program Files\\Cloudbase Solutions\\Cloudbase-Init\\conf\\cloudbase-init-unattend.conf" -Force')
#########################################sysprep instance ####################
out9 = session.run_cmd('%WINDIR%\system32\sysprep\sysprep.exe /generalize /shutdown /oobe')
print(colors.fg.blue,"\n Sysprep Command executed, system shuting down",colors.fg.green,out9.std_out,colors.reset)



