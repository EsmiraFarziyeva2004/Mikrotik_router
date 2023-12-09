import PySimpleGUI as sg
from netmiko import ConnectHandler
from time import sleep
from curses import ascii 

class MikrotikRouter:
    def __init__(self, host, username='admin', password='123',port=22):
        self.device_type = 'mikrotik_routeros'
        self.host = host 
        self.username = username
        self.password = password
        self.port = port
        self.config_set = None
        self.connenction = None
        
    def connect(self):
        self.config_set = {
            'device_type': self.device_type,
            'host': self.host,
            'username': self.username,
            'password': self.password,
            'port': self.port
        }
        self.connenction = ConnectHandler(**self.config_set)
        
    def disconnect(self):
        self.connenction.disconnect()

    def send_command(self, command):
        return self.connenction.send_command(command, cmd_verify=False)
    
    def send_str(self,string):
        self.connenction.write_channel(string)

theme1 = 'DarkPurple3'
theme2 = 'DarkPurple'
sg.theme(theme1)
button_color = ('white', 'blue')
size1 = (15, 1)
size2 = (8, 1)
size3 = (65, 15)
size4 = (20, 1)
title = 'Mikrotik Router Configuration'
retry_times = 4
sleep_time = 15
is_safe = False

def click_safe_mode():
    global is_safe
    if not is_safe: 
        sg.popup('Switching to Safe Mode...')
        sg.theme(theme2)
    else: 
        sg.popup('Exiting Safe Mode...')
        sg.theme(theme1)
    is_safe = not is_safe
    router.send_str(ascii.ctrl('x'))


def retry(method):
    for i in range(retry_times):
        try:
            method()
            break
        except Exception as e:
            sg.popup('Connection failed:  '+str(e)+'\nRetrying...')
            sleep(sleep_time)
            continue
    if retry_times == i+1:
        sg.popup('Connection failed.')
        return False
    return True

def show_anything(window, command):
    try:
        result = router.send_command(command)
        window['-Result-'].update(result)
    except Exception as e:
        sg.popup('Failed:  '+str(e))

def number_page(what_page,show_command, execute_command):
    result = router.send_command(show_command)
    new_window = sg.Window(title, [[sg.Text(what_page)],
        [sg.Text('Enter number',s=size4), sg.InputText(s=size1)],
        [sg.Button('Execute',s=size1)],
        [sg.Button('Back',s=size1)],
        [sg.Text('Result:',s=size2)], 
        [sg.Multiline(default_text=result, s=size3, key='-Result-')]] )
    while True:
        event, values = new_window.read()
        if event in (sg.WIN_CLOSED, 'Back'):
            break
        if event == 'Execute':
            try:
                number = values[0]
                result = router.send_command(execute_command+number) or 'Success'
                new_window['-Result-'].update(result)
            except Exception as e:
                sg.popup('Failed:  '+str(e))
            continue
    new_window.close()

def open_ip_page():
    window = sg.Window(title, [
        [sg.Text('IP Page')],
        [sg.Column([
            [sg.Button('Show IP address', size=size1, button_color=button_color)],
            [sg.Button('Add IP address', size=size1, button_color=button_color)],
        ]),
        sg.Column([
            [sg.Button('Change IP address', size=size1, button_color=button_color)],
            [sg.Button('Remove IP address', size=size1, button_color=button_color)],
        ]),
        sg.Column([
            [sg.Button('BACK', size=size1,button_color=('white','green'))],
        ])],
        [sg.Text('Result:', size=size2)],
        [sg.Multiline(size=size3, key='-Result-')]
    ])

    hidden = False
    while True:
        if hidden: window.un_hide()
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'BACK'):
            break
        if event == 'Show IP address':
            show_anything(window, '/ip address print')
            continue
        if event == 'Add IP address':
            window.hide()
            hidden = True
            result = router.send_command('/ip address print')
            new_window = sg.Window(title, [[sg.Text('Add IP address Page')],
                [sg.Text('Enter IP address (N.N.N.N/M)',s=size4), sg.InputText(s=size1)],
                [sg.Text('Enter interface(default ether2)',s=size4), sg.InputText(s=size1)],
                [sg.Button('Execute',s=size1)],
                [sg.Button('BACK', size=size1,button_color=('white','green'))],
                [sg.Text('Result:',s=size2)], 
                [sg.Multiline(default_text=result, s=size3, key='-Result-')]] )
            while True:
                event, values = new_window.read()
                if event in (sg.WIN_CLOSED, 'BACK'):
                    break
                if event == 'Execute':
                    try:
                        ip_address = values[0]
                        interface = values[1] or 'ether2'
                        result = router.send_command('/ip address add address='+ip_address+' interface='+interface) or 'Success'
                        new_window['-Result-'].update(result)
                    except Exception as e:
                        sg.popup('Failed:  '+str(e))
                    continue
            new_window.close()
            continue
        if event == 'Remove IP address':
            window.hide()
            hidden = True
            number_page('Remove IP address Page', '/ip address print', '/ip address remove numbers=')
            continue
        if event == 'Change IP address':
            result = router.send_command('/ip address print')
            window.hide()
            hidden = True
            new_window = sg.Window(title, [[sg.Text('Change IP address Page')],
                [sg.Text('Current IP address: '+router.host, key='-CURRENT-IP-')],
                [sg.Text('Enter IP address (N.N.N.N)',s=size4), sg.InputText(s=size1)],
                [sg.Button('Execute',s=size1)],
                [sg.Button('Back',s=size1,button_color=('white','green'))],
                [sg.Text('Result:',s=size2)], 
                [sg.Multiline(default_text=result, s=size3, key='-Result-')]] )
            while True:
                event, values = new_window.read()
                if event in (sg.WIN_CLOSED, 'Back'):
                    break
                if event == 'Execute':
                    try:
                        ip_address = values[0]
                        router.host = ip_address
                        if not retry(router.connect): continue
                        new_window['-Result-'].update('Success')
                        new_window['-CURRENT-IP-'].update('Current IP address: '+router.host)

                    except Exception as e:
                        sg.popup('Failed:  '+str(e))
                    continue
            new_window.close()
            continue
    window.close()

def open_port_page():
    window = sg.Window(title, [
        [sg.Text('Port Page')],
        [sg.Button('Change port', size=size1, button_color=button_color)],
        [sg.Button('Show port', size=size1, button_color=button_color)],
        [sg.Button('BACK', size=size1,button_color=('white','green'))],
        [sg.Text('Result:', size=size2)], 
        [sg.Multiline(size=size3, key='-Result-')]
    ])
    hidden = False
    while True:
        if hidden: window.un_hide()
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'BACK'):
            break
        if event == 'Show port':
            show_anything(window, '/ip service print')
            continue
        if event == 'Change port':
            result = router.send_command('/ip service print')
            window.hide()
            hidden = True
            new_window = sg.Window(title, [[sg.Text('Change port Page')],
                [sg.Text('Current port: '+str(router.port), key='-CURRENT-PORT-')],
                [sg.Text('Type the port you wish to retract (ssh by default)',s=size4), sg.InputText(s=size1)],
                [sg.Text('Enter new port number',s=size4), sg.InputText(s=size1)],
                [sg.Button('Execute',s=size1)],
                [sg.Button('Back',s=size1, button_color=('white','green'))],
                [sg.Text('Result:',s=size2)], 
                [sg.Multiline(default_text=result, s=size3, key='-Result-')]] )
            while True:
                event, values = new_window.read()
                if event in (sg.WIN_CLOSED, 'Back'):
                    break
                if event == 'Execute':
                    try:
                        port = values[0] or 'ssh'
                        port_number = values[1]
                        router.send_command(f'/ip service set {port} port={port_number}')
                        if port == 'ssh': 
                            if not retry(router.connect): continue
                        
                        new_window['-Result-'].update('Success')
                        new_window['-CURRENT-PORT-'].update('Current IP address: '+router.port)
                    except Exception as e:
                        sg.popup('Failed:  '+str(e))
                    continue
            new_window.close()
            continue
    window.close()

def open_firewall_page():
    window = sg.Window(title, [
        [sg.Text('Firewall Page')],
        [sg.Column([
            [sg.Button('Show firewall rule', size=size1, button_color=button_color)],
            [sg.Button('Add firewall rule', size=size1, button_color=button_color)],
            [sg.Button('Remove firewall rule', size=size1, button_color=button_color)]
        ]),
        sg.Column([
            [sg.Button('Disable firewall rule', size=size1, button_color=button_color)],
            [sg.Button('Enable firewall rule', size=size1, button_color=button_color)],
            [sg.Button('BACK', size=size1, button_color=('white', 'green'))]
        ])],
        [sg.Text('Result:', size=size2)], 
        [sg.Multiline(size=size3, key='-Result-')]
    ])

    hidden = False
    while True:
        if hidden:
            window.un_hide()
        event, values = window.read()

        if event in (sg.WIN_CLOSED, 'BACK'):
            break
        if event == 'Show firewall rule':
            show_anything(window, '/ip firewall filter print')
            continue
        if event == 'Add firewall rule':
            result = router.send_command('/ip firewall filter print')
            window.hide()
            hidden = True
            new_window = sg.Window(title, [
                [sg.Text('Add firewall rule Page')],
                [sg.Text('Enter rule (default: chain=forward)', s=size4), sg.InputText(s=size1)],
                [sg.Button('Execute', s=size1)],
                [sg.Button('Back', s=size1, button_color=('white', 'green'))],
                [sg.Text('Result:', s=size2)], 
                [sg.Multiline(default_text=result, s=size3, key='-Result-')]
            ])
            while True:
                event, values = new_window.read()
                if event in (sg.WIN_CLOSED, 'Back'):
                    break
                if event == 'Execute':
                    try:
                        rule = values[0] or 'chain=forward'
                        result = router.send_command('/ip firewall filter add ' + rule) or 'Success'
                        new_window['-Result-'].update(result)
                    except Exception as e:
                        sg.popup('Failed: ' + str(e))
                    continue
            new_window.close()
            continue
        if event == 'Remove firewall rule':
            window.hide()
            hidden = True
            number_page('Remove firewall rule Page', '/ip firewall filter print', '/ip firewall filter remove numbers=')
            continue
        if event == 'Disable firewall rule':
            window.hide()
            hidden = True
            number_page('Disable firewall rule Page', '/ip firewall filter print', '/ip firewall filter disable numbers=')
            continue
        if event == 'Enable firewall rule':
            window.hide()
            hidden = True
            number_page('Enable firewall rule Page', '/ip firewall filter print', '/ip firewall filter enable numbers=')
            continue

    window.close()



def open_info_page():
    window = sg.Window(title, [
        [sg.Text('Info Page')],
        [sg.Button('SYSTEM RESOURCE', size=size1, button_color=button_color),
         sg.Button('INTERFACE', size=size1, button_color=button_color),
         sg.Button('ROUTE', size=size1, button_color=button_color),
         sg.Button('ARP', size=size1, button_color=button_color),
         sg.Button('DNS', size=size1, button_color=button_color)],
        [sg.Button('USER', size=size1, button_color=button_color),
         sg.Button('LOG', size=size1, button_color=button_color),
         sg.Button('BACKUP CONFIG', size=size1, button_color=button_color),
         sg.Button('WIRELESS INFO', size=size1, button_color=button_color),
         sg.Button('SYSTEM HEALTH', size=size1, button_color=button_color)],
        [sg.Button('IPSEC INFO', size=size1, button_color=button_color),
         sg.Button('VPN INFO', size=size1, button_color=button_color),
         sg.Button('FIREWALL RULES', size=size1, button_color=button_color),
         sg.Button('NAT RULES', size=size1, button_color=button_color),
         sg.Button('SYSTEM IDENTITY', size=size1, button_color=button_color)],
        [sg.Button('IP SERVICES', size=size1, button_color=button_color),
         sg.Button('DISK USAGE', size=size1, button_color=button_color),
         sg.Button('PACKAGES INSTALLED', size=size1, button_color=button_color),
         sg.Button('SYSTEM CLOCK', size=size1, button_color=button_color),
         sg.Button('BACK', size=size1,button_color=('white','green'))],
        [sg.Text('RESULT:', size=size2)], 
        [sg.Multiline(size=size3, key='-Result-')]
    ])
    
    hidden = False
    while True:
        if hidden: window.un_hide()
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'BACK'):
            break
        elif event == 'SYSTEM RESOURCE':
            show_anything(window, '/system resource print')
            continue
        elif event == 'INTERFACE':
            show_anything(window, '/interface print')
            continue
        elif event == 'ROUTE':
            show_anything(window, '/ip route print')
            continue
        elif event == 'ARP':
            show_anything(window, '/ip arp print')
            continue
        elif event == 'DNS':
            show_anything(window, '/ip dns print')
            continue
        elif event == 'USER':
            show_anything(window, '/user print')
            continue
        elif event == 'LOG':
            show_anything(window, '/log print')
            continue
        elif event == 'WIRELESS INFO':
            show_anything(window, '/interface wireless print')
            continue
        elif event == 'SYSTEM HEALTH':
            show_anything(window, '/system health print')
            continue
        elif event == 'IPSEC INFO':
            show_anything(window, '/ip ipsec policy print')
            continue
        elif event == 'BACKUP CONFIG':
            show_anything(window, '/system backup save name=mybackup')
            continue
        elif event == 'VPN INFO':
            show_anything(window, '/interface pptp-server print')
            continue
        elif event == 'FIREWALL RULES':
            show_anything(window, '/ip firewall filter print')
            continue
        elif event == 'NAT RULES':
            show_anything(window, '/ip firewall nat print')
            continue
        elif event == 'SYSTEM IDENTITY':
            show_anything(window, '/system identity print')
            continue
        elif event == 'IP SERVICES':
            show_anything(window, '/ip service print')
            continue
        elif event == 'DISK USAGE':
            show_anything(window, '/file print detail')
            continue
        elif event == 'PACKAGES INSTALLED':
            show_anything(window, '/system package print')
            continue
        elif event == 'SYSTEM CLOCK':
            show_anything(window, '/system clock print')
            continue
    window.close()




def open_safe_page():
    window = sg.Window(title, [
        [sg.Text('Safe Page')],
        [sg.Button('Click safe mode', size=size1, button_color=button_color)],
        [sg.Button('BACK', size=size1,button_color=('white','green'))]
    ])

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, 'BACK'):
            break
        elif event == 'Click safe mode':
            click_safe_mode()
            window.close()
            window = sg.Window(title, [
                [sg.Text('Safe Page')],
                [sg.Button('Click safe mode', size=size1, button_color=button_color)],
                [sg.Button('BACK', size=size1,button_color=('white','green'))]
            ])
            continue

    window.close()

def open_any_command_page():
    window = sg.Window(title, [[sg.Text('Any command Page')],
        [sg.Text('Command',s=size2), sg.InputText(s=size1)],
        [sg.Button('Execute',s=size1)],
        [sg.Button('Back',s=size1,button_color=('white','green'))],
        [sg.Text('Result:',s=size2)], 
        [sg.Multiline(s=size3, key='-Result-')]])
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Back'):
            break
        if event == 'Execute':
            try:
                result = router.send_command(values[0])
                window['-Result-'].update(result)
            except Exception as e:
                sg.popup('Failed:  '+str(e))
    window.close()
    del window

def open_main_page():
    layout = [
        [sg.Text('Main Page')],
        [sg.Column([
            [sg.Button('IP address', size=size1)],
            [sg.Button('Port', size=size1)]
            
        ]),
        sg.Column([
            [sg.Button('Firewall rules', size=size1)],
            [sg.Button('General info', size=size1)]
            
        ]),
        sg.Column([
            [sg.Button('Safe mode', size=size1)],
            [sg.Button('Exit', size=size1)]
        ])]
    ]

    window = sg.Window(title, layout)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        if event == 'IP address':
            open_ip_page()
        elif event == 'Port':
            open_port_page()
        elif event == 'Firewall rules':
            open_firewall_page()
        elif event == 'General info':
            open_info_page()
        elif event == 'Safe mode':
            open_safe_page()

    window.close()


layout_login = [
    [sg.Text('Login to Mikrotik Router', font=('Helvetica', 20))],
    [sg.Text('Router IP:', size=(10, 1), font=('Helvetica', 14)), sg.InputText(size=(20, 1), key='-HOST-')],
    [sg.Text('Router Port:', size=(10, 1), font=('Helvetica', 14)), sg.InputText(size=(20, 1), key='-PORT-')],
    [sg.Text('Username:', size=(10, 1), font=('Helvetica', 14)), sg.InputText(size=(20, 1), key='-USERNAME-')],
    [sg.Text('Password:', size=(10, 1), font=('Helvetica', 14)), sg.InputText(size=(20, 1), password_char='*', key='-PASSWORD-')],
    [sg.Button('Login', size=(10, 1), button_color=('white', 'green'))]
]

window_login = sg.Window(title, layout_login)

while True:
    event, values = window_login.read()

    if event in (sg.WIN_CLOSED, 'Exit'):
        break

    if event == 'Login':
        host = values['-HOST-'] or '192.168.56.56'
        port = values['-PORT-'] or 22
        username = values['-USERNAME-'] or 'admin'
        password = values['-PASSWORD-']

        router = MikrotikRouter(host, username, password, port)

        for i in range(retry_times):
            try:
                router.connect()
                break
            except Exception as e:
                sg.popup('Login failed: ' + str(e) + '\nRetrying...')
                sleep(sleep_time)
                continue

        if retry_times == i + 1:
            sg.popup('Login failed\nPlease check your network and try again')
            continue

        sg.popup('You have successfully connected!')
        window_login.close()
        open_main_page()
        break

window_login.close()