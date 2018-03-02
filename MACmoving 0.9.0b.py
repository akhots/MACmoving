# MAC moving. Written on Python 3.6
print('MAC moving 0.9.0b  Developed by AKhotsyanovskiy\r\n')

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

mainList = []
macEnd = '0'
print('Enter list of MAC addresses or their end part')
while macEnd != '':
	macEnd = input(': ').lower().replace(':','').replace('-','').replace(' ','').replace('\t','')
	if len(macEnd) == 0:
		print('Searching...')
	elif len(macEnd) < 3:
		print('Bad input')
	elif macEnd != '':
		mainList.append(macEnd)
# -------------------------------- input --------------------------------

if len(mainList) == 0:
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

for one in range(len(mainList)):
	out = connectSession.send_command('sh mac add | in .......' + mainList[one] + '_').split('\n')
	if out == ['']:
		mainList[one] = ['-','No MAC found',mainList[one]]
	elif len(out) == 1:
		out = out[0].split()
		mainList[one] = [out[0],out[1],mainList[one]]
	elif len(out) >= 1:
		print('\r\nThere are more than one MAC with "' + str(mainList[one]) + '" in the end')
		print('\r\nLine  Vlan    Mac Address       Type        Port on CoreSW')
		for two in range(len(out)):
			print(str(two + 1) + "     " + out[two].replace('\r\n',''))
		out = out[int(input("\r\nChoose line: ")) - 1].split()
		mainList[one] = [out[0],out[1],mainList[one]]
# -------------------------------- input --------------------------------

for one in range(len(mainList)):
	if mainList[one][0] != '-':
		macFull = mainList[one][1]
		oldVLAN = mainList[one][0]
		out = connectSession.send_command('trac mac ' + macFull + ' ' + macFull + ' vlan ' + oldVLAN)
		if len(out.split('\n')) == 4:
			out = out.split('\n')[1].split()
			mainList[one].append(out[1])
			mainList[one].append(out[2].replace('(','').replace(')',''))
			mainList[one].append(out[-1])
		else:
			mainList[one].append('No switch found')
			mainList[one].append('-')

connectSession.disconnect()

print('\r\nVlan   MAC address         Switch (IP)                       Port')
for one in range(len(mainList)):
	if len(mainList[one]) == 3:
		print(mainList[one][0].ljust(7) + 'No MAC found (' + mainList[one][2] + ')')
	elif '-' in mainList[one]:
		print(mainList[one][0].ljust(7) + mainList[one][1].ljust(20) + mainList[one][3])
	else:
		swNameIP = mainList[one][3] + ' ( ' + mainList[one][4] + ' )'
		print(mainList[one][0].ljust(7) + mainList[one][1].ljust(20) + swNameIP.ljust(34) + mainList[one][5])

newVLAN = 0

def vlanTest(a):
	try:
		a = int(a)
		return a
	except:
		return 0

for one in mainList:
	if '-' not in one:
		while newVLAN <= 0 or newVLAN >= 4095:
			newVLAN = input('\r\nEnter VLAN, to which you want to move MAC addresses: ').replace(' ','')
			newVLAN = vlanTest(newVLAN)
			if newVLAN <= 0 or newVLAN >= 4095:
				print(' Wrong entry!')
# -------------------------------- input --------------------------------

for one in mainList:
	if len(one) != 6:
		one.clear()

while [] in mainList:
	mainList.remove([])

for one in mainList:
	two = one[4]
	one.remove(two)
	one.insert(0,two)

mainList.sort()

swList = []
for one in mainList:
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
		for one in mainList:
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
