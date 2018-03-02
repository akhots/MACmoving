# MAC moving. Written on Python 3.6
print('MAC moving 0.9.1b  Developed by AKhotsyanovskiy\r\n')

import getpass
try:
	from netmiko import ConnectHandler
except:
	print(' Need to install netmiko package.\r\n Command line: "pip install netmiko"')
	input('\r\nPress Enter to exit...')
	quit()

#switch = "172.30.29.1"
switch = input("Enter core switch: ")
# -------------------------------- input --------------------------------
login = "akhotsyanovskiy"
#login = input("Enter login: ")
password = getpass.getpass("Enter password: ")
# -------------------------------- input --------------------------------

macList = 'Null'
print('Enter list of MAC addresses or their end part:')
macLine = input()
#---------------------------------input---------------------------------
while macLine != '':
	macList = macList + ',' + macLine
	macLine = input()
#---------------------------------input---------------------------------

macList = macList.replace(';',',')
macList = macList.replace('Null,','')
macList = macList.replace('-','').replace(':','').replace(' ','').replace('.','').replace('\t','')

if macList == 'Null':
	input('\r\nNo MAC address entered\r\nPress Enter to exit...')
	quit()

macList = macList.lower()
macList = macList.split(',')

for one in macList:
	try:
		if int(one,16) >= 0xffffffffffff:
			raise
		elif len(one) <= 2:
			raise
	except:
		macList.remove(one)
		print(one + ' - Wrong MAC address!')


for one in range(len(macList)):
	if int(macList[one],16) > 0xffffffff:
		macList[one] = macList[one][:-8] + '.' + macList[one][-8:-4] + '.' + macList[one][-4:]
	elif int(macList[one],16) > 0xffff:
		macList[one] = macList[one][:-4] + '.' + macList[one][-4:]


if len(macList) > 0:
	print('\r\nSearching...')

if len(macList) == 0:
	input('\r\nNo MAC address entered\r\nPress Enter to exit...')
	quit()

authSW = {
	'device_type': 'cisco_ios',
	'ip': switch,
	'username': login,
	'password': password,
}

try:
	connectSession = ConnectHandler(**authSW)
except:
	input('\r\n Failed to connect\r\n\r\nPress Enter to exit...')
	quit()

for one in range(len(macList)):
	out = connectSession.send_command('sh mac add | in .......' + macList[one] + '_').split('\n')
	if out == ['']:
		macList[one] = ['-','No MAC found',macList[one]]
	elif len(out) == 1:
		out = out[0].split()
		macList[one] = [out[0],out[1],macList[one]]
	elif len(out) >= 1:
		print('\r\nThere are more than one MAC with "' + str(macList[one]) + '" in the end')
		print('\r\nLine  Vlan    Mac Address       Type        Port on CoreSW')
		for two in range(len(out)):
			print(str(two + 1) + "     " + out[two].replace('\r\n',''))
		out = out[int(input("\r\nChoose line: ")) - 1].split()
		macList[one] = [out[0],out[1],macList[one]]
# -------------------------------- input --------------------------------

for one in range(len(macList)):
	if macList[one][0] != '-':
		macFull = macList[one][1]
		oldVLAN = macList[one][0]
		out = connectSession.send_command('trac mac ' + macFull + ' ' + macFull + ' vlan ' + oldVLAN)
		if len(out.split('\n')) == 4:
			out = out.split('\n')[1].split()
			macList[one].append(out[1])
			macList[one].append(out[2].replace('(','').replace(')',''))
			macList[one].append(out[-1])
		else:
			macList[one].append('No switch found')
			macList[one].append('-')

connectSession.disconnect()

print('\r\nVlan   MAC address         Switch (IP)                       Port')
for one in range(len(macList)):
	if len(macList[one]) == 3:
		print(macList[one][0].ljust(7) + 'No MAC found (' + macList[one][2] + ')')
	elif '-' in macList[one]:
		print(macList[one][0].ljust(7) + macList[one][1].ljust(20) + macList[one][3])
	else:
		swNameIP = macList[one][3] + ' ( ' + macList[one][4] + ' )'
		print(macList[one][0].ljust(7) + macList[one][1].ljust(20) + swNameIP.ljust(34) + macList[one][5])

newVLAN = 0

def vlanTest(a):
	try:
		a = int(a)
		return a
	except:
		return 0

for one in macList:
	if '-' not in one:
		while newVLAN <= 0 or newVLAN >= 4095:
			newVLAN = input('\r\nEnter VLAN, to which you want to move MAC addresses: ').replace(' ','')
			newVLAN = vlanTest(newVLAN)
			if newVLAN <= 0 or newVLAN >= 4095:
				print(' Wrong entry!')
# -------------------------------- input --------------------------------

for one in macList:
	if len(one) != 6:
		one.clear()

while [] in macList:
	macList.remove([])

for one in macList:
	two = one[4]
	one.remove(two)
	one.insert(0,two)

macList.sort()

swList = []
for one in macList:
	swList.append(one[0])

for one in range(len(swList)-1):
	if swList[one] == swList[one+1]:
		swList[one] = ''

while '' in swList:
	swList.remove('')

def yesNo(a):
	a = a.lower()
	if a == 'yes' or a == 'y':
		a = True
	else:
		a = False
	return a

intReboot = yesNo(input('\r\nReboot the ports [no]? '))
# -------------------------------- input --------------------------------
confSave = yesNo(input('Save configuration on switches [no]? '))
# -------------------------------- input --------------------------------
agree = yesNo(input('\r\nAre you sure you want to move MAC addresses [no]? '))
# -------------------------------- input --------------------------------
if agree == False:
	input('\r\nPress Enter to exit...')
	quit()

print('\r\nStart moving...\r\n')

for switch in swList:
	authSW['ip'] = switch
	try:
		connectSession = ConnectHandler(**authSW)
		for one in macList:
			if switch in one:
				if intReboot:
					connectSession.send_config_set([
						'int ' + one[-1],
						'sw ac vl ' + str(newVLAN),
						'sh',
						'no sh'
					])
				else:
					connectSession.send_config_set([
						'int ' + one[-1],
						'sw ac vl ' + str(newVLAN)
					])
				print(switch + ' / ' + one[-1] + ' - OK')
		if confSave:
			connectSession.send_command_expect('wr')
		connectSession.disconnect()
	except:
		print(switch + ' - Failed to connect')
# -------------------------------- input --------------------------------

input('\r\nDone!\r\n\r\nPress Enter to exit...')
