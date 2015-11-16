import json
import yaml
import time

DB_FILE = 'pi-pinout.yaml'
SETTINGS_FILE = 'settings.yaml'

pins = None
settings = None

def get_setting(setting, default = None):
    if setting in settings and settings[setting] != None:
        return settings[setting]
    return default

def render_html(*args, **kwargs):
    html = args[0]
    kwargs['v'] = str(int(time.time()))
    for key in kwargs:
        html = html.replace('{{' + key + '}}', kwargs[key])
    return html

def bcm_to_physical(pin_num):
    for idx in pins:
        compare_pin = pins[idx]
        if 'scheme' in compare_pin:
            if 'bcm' in compare_pin['scheme']:
                if compare_pin['scheme']['bcm'] == pin_num:
                    #print("Mapping BCM{} to {}".format(pin_num, idx))
                    return idx

def physical_to_bcm(pin_num):
    pin = pins[pin_num]
    if 'scheme' in pin:
        if 'bcm' in pin['scheme']:
            return pin['scheme']['bcm']
    return None

def physical_to_wiringpi(pin_num):
    pin = pins[pin_num]
    if 'scheme' in pin:
        if 'wiringpi' in pin['scheme']:
            return pin['scheme']['wiringpi']
    return None

def physical_to(pin_num, scheme='bcm'):
    if scheme in ['bcm','wiringpi']:
        pin = pins[pin_num]
        if 'scheme' in pin:
            if scheme in pin['scheme']:
                return pin['scheme'][scheme]
    elif scheme == 'physical':
        return pin
    return None

def load(lang='en'):
    global pins, settings
    if DB_FILE.endswith('.yaml'):
        db = yaml.load(open('src/{}/{}'.format(lang,DB_FILE)).read())
    else:
        db = json.load(open('src/{}/{}'.format(lang,DB_FILE)))
    if SETTINGS_FILE.endswith('.yaml'):
        settings = yaml.load(open('src/{}/{}'.format(lang,SETTINGS_FILE)).read())
    else:
        settings = json.load(open('src/{}/{}'.format(lang,SETTINGS_FILE)))
    pins = dict()
    for str_pin in db['pins'].keys():
        pin = db['pins'][str_pin]
        if 'scheme' in pin:
            for scheme in pin['scheme']:
                pin['scheme'][scheme] = int(pin['scheme'][scheme])
        pin_num = int(str_pin)
        pins[pin_num] = pin


