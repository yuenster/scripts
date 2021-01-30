import sys
import re
import socket
from netmiko import ConnectHandler
from netmiko.ssh_exception import NetMikoAuthenticationException, NetMikoTimeoutException
from getpass import getpass
from datetime import datetime


# prints output to console and writes to log file
def showresult(result, hostname, logfile):
    outfile = open('%s%s' % (hostname, logfile), 'w')
    # get datetime
    dtime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    outfile.write('OUTPUT RETRIEVED ON %s VIA quickfetch.py\n' % dtime + ('-' * 60) + '\n\n')
    print('\n', '*' * 30, 'RESULTS', '*' * 30, '\n')
    for r in result:
        print(r)
        outfile.write('%s\n' % r)
    outfile.write('\n' + ('-' * 60) + '\nEND OF RESULTS')
    print('\n', '*' * 30, 'END OF RESULTS', '*' * 30)

    # print datetime and output file name to console
    print('\n\nCURRENT DATETIME IS %s \nOUTPUT WRITTEN TO %s%s' % (dtime, hostname, logfile))


# second pass of result parsing for user choice 3
# this function returns all interfaces that are line protocol up
def connected(f, newlist):
    if ' protocol is up' in f:
        newlist.append(f)
    else:
        return


# second pass of result parsing for user choice 2
# this function filters only interfaces with NO traffic (packets = 0), append to newList
def filtered0(f, newlist):
    # packet input lines: if no packet input, delete its respective interface
    if re.match(r'^[^\d]*([1-9]\d+)( packets in).*', f) is not None:  # match more than 0 packets
        if newlist:  # list is not empty
            del newlist[-1]
            return
        else:
            return
    elif 'line prot' in f:
        newlist.append(f)
    else:
        return


# second pass of result parsing for user choice 1
# this function filters ONLY interfaces containing traffic (packets > 0)
def filtered(f, newlist):
    # packet input lines: if no packet input, delete its respective interface
    if ' 0 packets input' in f:
        del newlist[-1]
        return True
    else:
        newlist.append(f)


# first pass of result parsing for user choices 1-3, returns results as newList
def getkeylines(net_connect, uinput):  # takes connection and user input option
    lines = net_connect.send_command("show int")  # uses results from the "show int" command for parsing
    lines = lines.splitlines()
    newlist = []
    templist = []

    re1 = '^[^ ].*'  # match lines starting with 1 whitespace (gets the interface line)
    re2 = '.*(packets input|packets output|multicasts).*'  # match lines with packet info

    for line in lines:
        output = re.compile("(%s|%s)" % (re1, re2)).findall(line)

        if output:
            for (x, y) in output:  # re.compile turned output into a tuple, we only care about output[0]
                if uinput == 1:
                    # this function filters only interfaces with traffic (packets > 0), append to newlist
                    templist.append(output[0][0])
                    # GOTO line 86 templist for loop
                elif uinput == 2:
                    # this function filters only interfaces with NO traffic (packets = 0), append to newlist
                    filtered0(x, newlist)

                elif uinput == 3:
                    # this function returns all interfaces that are line protocol up
                    connected(x, newlist)

    if uinput == 1:
        for i, li in enumerate(templist):
            skip = filtered(li,
                            newlist)  # this function filters only interfaces with traffic (packets > 0), append to newList
            if skip:  # if bool skip is true, skip next two elements in templist to clear 0 packet interface lines
                templist.pop(i + 1)
                templist.pop(i + 1)

    return newlist


def main():
    # option to enter hostname ip as first arg
    while True:
        try:
            script = sys.argv[0]
            host = sys.argv[1]
        except IndexError:
            host = input('Hostname IP: ')

        try:
            socket.inet_pton(socket.AF_INET, host)

            print('''
                            ***Cisco QuickFetch Script***
                    This script only works on Cisco IOS (for now)
                List of supported vendors with Netmiko can be found here:
        https://github.com/ktbyers/netmiko/blob/master/netmiko/ssh_dispatcher.py#L87
        
                ''')
            break
        except socket.error:
            print("You must enter a valid IP")

    # FOR FUTURE USE?
    # *******************************
    # *******************************
    # typeOption = int(input('''
    # Device, OS, and con type (input 0-6):
    #     0: Cisco ASA (SSH)
    #     1: Cisco IOS (SSH)
    #     2: Cisco IOS (TTY)
    #     3: Cisco IOS-XE (SSH)
    #     4: Cisco IOS-XR (SSH)
    #     5: Cisco IOS-XR (TTY)
    #     6: Cisco NX-OS (SSH)
    # '''))

    # devices = ['cisco_asa', 'cisco_ios', 'cisco_ios_telnet', 'cisco_xe', 'cisco_xr', 'cisco_xr_telnet', 'cisco_nxos']
    # *******************************
    # *******************************

    # continue prompting user until credentials are accepted
    while True:
        try:
            print('*Login to device*\n')
            user = input('Username: ')
            passw = getpass()
            connect = {
                'device_type': 'cisco_ios',
                'host': host,
                'username': user,
                'password': passw,
            }
            print('\nConnecting to', host, 'with user', user, 'via SSH on port 22...')
            net_connect = ConnectHandler(**connect)
            break
        except (NetMikoAuthenticationException, NetMikoTimeoutException):  # no ssh port, try telnet?
            try:
                print('SSH failed, trying Telnet on port 23...')
                connect['device_type'] = 'cisco_ios_telnet'
                net_connect = ConnectHandler(**connect)
                break
            except:  # no ssh or telnet, credentials wrong?
                print('\nInvalid Credentials, please try again\n\n')
                continue

    hostname = net_connect.find_prompt()[:-1]
    print('\nSuccessfully connected to', hostname)

    # get user selection and send to getkeylines() to parse and return the result
    # showresult() displays result to console and logfile
    while True:
        choice = input('''
        
What would you like to fetch (choice: 1-5)?
1 - Get all ports with a packet count OVER 0 (1+ input packets)
2 - Get all ports with packet count of 0
3 - Get all connected ports (up/up)
4 - Get result from custom Cisco IOS command
5 - Exit

Your choice: 
''')
        if choice == '1':
            print('\nGetting all ports with a packet count OVER 0 (1+ input packets)...\n\n')
            result = getkeylines(net_connect, 1)
            showresult(result, hostname, '_YES-TRAFFIC.log')

        elif choice == '2':
            print('\nGetting all ports with packet count of 0...\n\n')
            result = getkeylines(net_connect, 2)
            showresult(result, hostname, '_NO-TRAFFIC.log')

        elif choice == '3':
            print('\nGetting all connected ports (up/up)...\n\n')
            result = getkeylines(net_connect, 3)
            showresult(result, hostname, '_CONNECTED.log')

        elif choice == '4':
            while True:
                # Keep prompting user for a successful command
                customcom = input('Custom command: ')
                customarr = customcom.split()
                result = net_connect.send_command(customcom)
                customname = '_' + '-'.join(customarr).upper() + '.log'
                # '% ' represents error in custom command
                if '% ' in result:
                    print('Unrecognized command, please try again\n')
                    continue
                result = result.splitlines()
                outfilename = input(
                    'Name of output file? (If empty, default is ' + hostname + customname + ')\n\n')
                # if user did not enter custom name, use default, otherwise use custom name
                if outfilename != '':
                    showresult(result, outfilename, '.log')
                    break
                else:
                    showresult(result, hostname, customname)
                    break

        elif choice == '5' or '':
            print('\nGoodbye')
            break

        else:
            print('\nUnknown input, please input 1-5')


main()
