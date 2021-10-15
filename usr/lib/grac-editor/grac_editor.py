#!/usr/bin/env python3

#-------------------------------------------------------------------------------
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

import simplejson as json
import traceback
import gettext
import shutil
import signal
import dbus
import sys
import os

from ge_define import *

gettext.install('grac-editor', '/usr/share/gooroom/locale')

#-------------------------------------------------------------------------------
cssProvider = Gtk.CssProvider()
cssProvider.load_from_path('/usr/lib/grac-editor/theme.css')
screen = Gdk.Screen.get_default()
styleContext = Gtk.StyleContext()
styleContext.add_provider_for_screen(screen, cssProvider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

LBL_ALLOW = _('allow')
LBL_DISALLOW = _('disallow')

#-------------------------------------------------------------------------------
class GracEditor:
    """
    GRAC EDITOR
    """

    def __init__(self):

        #SET DESKTOP ICON
        Gdk.set_program_class('grac-editor')

        #LOAD RULES
        self.media_rules = self.load_rules(DEFAULT_RULES_PATH)

        #BUILDER
        self.builder = Gtk.Builder()
        self.builder.add_from_file(GLADE_PATH)
        self.builder.connect_signals(self)

        #WINDOW MAIN
        self.window_main = self.builder.get_object('window_main')

        #SHOW
        self.window_main.show_all()

        #DRAW MEDIA
        self.draw_media(self.media_rules)

        #LANG
        self.lang()

    def logging(self, txt):
        """
        write on textview_log
        """

        buff = self.builder.get_object('txtvw_log').get_buffer()
        ei = buff.get_end_iter()
        buff.insert(ei, txt+'\n')
        ei = buff.get_end_iter()
        mark = buff.create_mark('end', ei, False)
        buff = self.builder.get_object('txtvw_log').scroll_to_mark(
                                                        mark, 
                                                        0.05,
                                                        True,
                                                        0.0,0.0)

    def write_txtvw(self, vw_id, txt):
        """
        """

        buff = self.builder.get_object(vw_id).get_buffer()
        si = buff.get_start_iter()
        ei = buff.get_end_iter()
        buff.delete(si, ei)

        buff = self.builder.get_object(vw_id).get_buffer()
        ei = buff.get_end_iter()
        buff.insert(ei, txt)

    def read_txtvw(self, vw_id):
        """
        """

        buff = self.builder.get_object(vw_id).get_buffer()
        si = buff.get_start_iter()
        ei = buff.get_end_iter()
        return buff.get_text(si, ei, True)

    def draw_media(self, rules):
        """
        """

        for k, v in rules.items():
            #SWITCH
            swtch = self.builder.get_object('swtch+{}'.format(k))
            if swtch:
                if v[JSON_RULE_STATE] == JSON_RULE_ALLOW:
                    swtch.set_state(True)
                elif v[JSON_RULE_STATE] == JSON_RULE_READONLY:
                    swtch.set_state(False)
                    ckb = self.builder.get_object('ckb+{}'.format(k))
                    if ckb:
                        ckb.set_active(True)
                else:
                    swtch.set_state(False)
            else:
                pass

            #SWITCH LABEL
            swtch_state = self.builder.get_object('lbl+{}+state'.format(k))
            if swtch_state:
                if v[JSON_RULE_STATE] == JSON_RULE_ALLOW:
                    state = LBL_ALLOW
                else:
                    state = LBL_DISALLOW
                swtch_state.set_text(state)
            else:
                pass

            #WHITE LIST
            if k == JSON_RULE_USB_MEMORY and JSON_RULE_USB_SERIALNO in v:
                self.write_txtvw(
                    'txtvw_usb_whitelist', 
                    '\n'.join(self.media_rules[JSON_RULE_USB_MEMORY][JSON_RULE_USB_SERIALNO]))
            if k == JSON_RULE_BLUETOOTH and JSON_RULE_MAC_ADDRESS in v:
                self.write_txtvw(
                    'txtvw_bluetooth_whitelist', 
                    '\n'.join(self.media_rules[JSON_RULE_BLUETOOTH][JSON_RULE_MAC_ADDRESS]))
            if k == JSON_RULE_USB_NETWORK and JSON_RULE_USB_NETWORK_WHITELIST in v:
                ent_unw = self.builder.get_object('ent_usb_network_whitelist')
                wls = self.media_rules[JSON_RULE_USB_NETWORK][JSON_RULE_USB_NETWORK_WHITELIST]
                for name, contents in wls.items():
                    if name == 'usbbus':
                        ent_unw.set_text(contents)
                        break
                else:
                    ent_unw.set_text('')

            #WHITE LIST SENSITIVE
            if k == JSON_RULE_USB_MEMORY and v[JSON_RULE_STATE] == JSON_RULE_ALLOW:
                self.builder.get_object('txtvw_usb_whitelist').set_sensitive(False)
                self.builder.get_object('ckb+{}'.format(JSON_RULE_USB_MEMORY)).set_sensitive(False)
            if k == JSON_RULE_BLUETOOTH and v[JSON_RULE_STATE] == JSON_RULE_ALLOW:
                self.builder.get_object('txtvw_bluetooth_whitelist').set_sensitive(False)
            if k == JSON_RULE_USB_NETWORK and v[JSON_RULE_STATE] == JSON_RULE_ALLOW:
                self.builder.get_object('ent_usb_network_whitelist').set_sensitive(False)

            #IPTABLES
            if k == JSON_RULE_NETWORK and JSON_RULE_NETWORK_RULES_RAW in v:
                rules_raw = v[JSON_RULE_NETWORK_RULES_RAW]
                rules_raw = [(int(rule_raw['seq']), rule_raw['cmd']) for rule_raw in rules_raw]
                rules_raw = sorted(rules_raw, key=lambda i:i[0])

                txt = ''
                for rr in rules_raw:
                    txt += rr[1] + '\n'
                if txt:
                    self.write_txtvw('txtvw_iptables', txt)
                    
                
    def load_rules(self, rule_path):
        """
        load rules file
        """
        
        with open(rule_path) as f:
            json_rules = json.loads(f.read())

        new_json_rules = {}

        for k, v in json_rules.items():
            state = None
            if isinstance(v, str):
                new_json_rules[k] = {}
                new_json_rules[k][JSON_RULE_STATE] = v
            else:
                new_json_rules[k] = {}
                for k2, v2 in v.items():
                    new_json_rules[k][k2] = v2

        return new_json_rules

    def on_swtch_usb_memory_button_release_event(self, obj, e):
        """
        """

        if not obj.get_active():
            self.builder.get_object('txtvw_usb_whitelist').set_sensitive(False)
            self.builder.get_object('ckb+{}'.format(JSON_RULE_USB_MEMORY)).set_sensitive(False)
            self.builder.get_object('ckb+{}'.format(JSON_RULE_USB_MEMORY)).set_active(False)
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_USB_MEMORY)).set_text(LBL_ALLOW)
        else:
            self.builder.get_object('txtvw_usb_whitelist').set_sensitive(True)
            self.builder.get_object('ckb+{}'.format(JSON_RULE_USB_MEMORY)).set_sensitive(True)
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_USB_MEMORY)).set_text(LBL_DISALLOW)

    def on_swtch_printer_button_release_event(self, obj, e):
        """
        """

        if not obj.get_active():
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_PRINTER)).set_text(LBL_ALLOW)
        else:
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_PRINTER)).set_text(LBL_DISALLOW)

    def on_swtch_cd_dvd_button_release_event(self, obj, e):
        """
        """

        if not obj.get_active():
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_CD_DVD)).set_text(LBL_ALLOW)
        else:
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_CD_DVD)).set_text(LBL_DISALLOW)

    def on_swtch_camera_button_release_event(self, obj, e):
        """
        """

        if not obj.get_active():
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_CAMERA)).set_text(LBL_ALLOW)
        else:
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_CAMERA)).set_text(LBL_DISALLOW)

    def on_swtch_sound_button_release_event(self, obj, e):
        """
        """

        if not obj.get_active():
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_SOUND)).set_text(LBL_ALLOW)
        else:
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_SOUND)).set_text(LBL_DISALLOW)

    def on_swtch_microphone_button_release_event(self, obj, e):
        """
        """

        if not obj.get_active():
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_MICROPHONE)).set_text(LBL_ALLOW)
        else:
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_MICROPHONE)).set_text(LBL_DISALLOW)

    def on_swtch_wireless_button_release_event(self, obj, e):
        """
        """

        if not obj.get_active():
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_WIRELESS)).set_text(LBL_ALLOW)
        else:
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_WIRELESS)).set_text(LBL_DISALLOW)

    def on_swtch_bluetooth_button_release_event(self, obj, e):
        """
        """

        if not obj.get_active():
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_BLUETOOTH)).set_text(LBL_ALLOW)
            self.builder.get_object('txtvw_bluetooth_whitelist').set_sensitive(False)
        else:
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_BLUETOOTH)).set_text(LBL_DISALLOW)
            self.builder.get_object('txtvw_bluetooth_whitelist').set_sensitive(True)

    def on_swtch_keyboard_button_release_event(self, obj, e):
        """
        """

        if not obj.get_active():
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_KEYBOARD)).set_text(LBL_ALLOW)
        else:
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_KEYBOARD)).set_text(LBL_DISALLOW)

    def on_swtch_mouse_button_release_event(self, obj, e):
        """
        """

        if not obj.get_active():
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_MOUSE)).set_text(LBL_ALLOW)
        else:
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_MOUSE)).set_text(LBL_DISALLOW)

    def on_swtch_screen_capture_button_release_event(self, obj, e):
        """
        """

        if not obj.get_active():
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_SCREEN_CAPTURE)).set_text(LBL_ALLOW)
        else:
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_SCREEN_CAPTURE)).set_text(LBL_DISALLOW)

    def on_swtch_clipboard_button_release_event(self, obj, e):
        """
        """

        if not obj.get_active():
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_CLIPBOARD)).set_text(LBL_ALLOW)
        else:
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_CLIPBOARD)).set_text(LBL_DISALLOW)

    def on_swtch_usb_network_button_release_event(self, obj, e):
        """
        """

        if not obj.get_active():
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_USB_NETWORK)).set_text(LBL_ALLOW)
            self.builder.get_object('ent_usb_network_whitelist').set_sensitive(False)
        else:
            self.builder.get_object('lbl+{}+state'.format(JSON_RULE_USB_NETWORK)).set_text(LBL_DISALLOW)
            self.builder.get_object('ent_usb_network_whitelist').set_sensitive(True)

    def on_window_main_destroy(self, obj):
        """
        destroy window main
        """

        Gtk.main_quit()

    def validate_whitelist_bluetooth(self, txt):
        """
        validate bluetooth of whitelist
        """

        if not txt:
            return VALIDATE_OK

        err_msg = _('invalid mac format(ex 01:23:45:ab:cd:ef)')
        macs = [t.strip() for t in txt.strip('\n').split('\n')]
        for mac in macs:
            s_mac = mac.split(':')
            if len(s_mac) != 6:
                return err_msg #+ ':mac items != 6'
            for m in s_mac:
                if len(m) != 2:
                    return err_msg #+ ':len(mac) != 2'
                m0 = ord(m[0].lower())
                m1 = ord(m[1].lower())
                for m in (m0, m1):
                    if (m >= ord('0') and m <= ord('9')) or \
                        (m >= ord('a') and m <= ord('f')):
                        pass
                    else:
                        return err_msg #+ ':wrong character'

        return VALIDATE_OK

    def ip_type(self, ip):
        """
        check ipv4 | ipv6 | domain
        """

        try:
            it = ipaddress.ip_address(ip)
            if isinstance(it, ipaddress.IPv4Address):
                return 'v4'
            return 'v6'
        except:
            return 'domain'

    def validate_network(self, address, src_port, dst_port):
        """
        validate address and ports
        """

        if not any((address, src_port, dst_port)):
            return _('need address or port')

        '''
        if self.ip_type(address) == 'domain':
            #once domain is considred as success
            pass
        else:
            #validate ip
            ip = address
            err_msg = 'invalid ip format'

            ip_items = [i.strip() for i in ip.split('.')]
            if len(ip_items) != 4:
                return err_msg + ':items != 4'

            try:
                for item in ip_items:
                    int_item = int(item)
                    if int_item < 0 or int_item > 255:
                        return err_msg + ':item<0 or item>255'
            except:
                return err_msg + ':maybe items not digit'
        '''

        #validate port
        err_msg = 'invalid port format(1-65535)'

        src_port_items = []
        dst_port_items = []
        if src_port:
            src_port_items = [i.strip() for i in src_port.split(',')]
        if dst_port:
            dst_port_items = [i.strip() for i in dst_port.split(',')]

        for port_items in (src_port_items, dst_port_items):
            try:
                for item in port_items:
                    if '-' in item:
                        left, right = [i.strip() for i in item.split('-')]
                        int_left = int(left)
                        int_right = int(right)
                        if int_left < 1 or int_left >= 65536 or int_right < 1 or int_right >= 65536:
                            return err_msg #+ ':ranged-item<1 or ranged-item>65536'
                    else:
                        int_item  = int(item)
                        if int_item < 1 or int_item >= 65536:
                            return err_msg #+ ':item<1 or item>65536'
            except:
                return err_msg #+ ':maybe items not digit or wrong ranged format'
                
        return VALIDATE_OK

    def on_menu_remove_user_rule_activate(self, obj):
        """
        menu > File > remove user rule
        """

        USER_RULE_PATH = '/etc/gooroom/grac.d/user.rules'
        if os.path.exists(USER_RULE_PATH):
            os.remove(USER_RULE_PATH)
        self.logging(_('removing success'))

        try:
            system_bus = dbus.SystemBus()
            bus_object = system_bus.get_object(DBUS_NAME, DBUS_OBJ)
            bus_interface = dbus.Interface(bus_object, dbus_interface=DBUS_IFACE)
            bus_interface.reload('')
            self.logging(_('apply success'))
        except:
            self.logging(raceback.format_exc())
            self.logging(_('apply fail'))

    def on_menu_save_activate(self, obj):
        """
        menu > File > save
        """

        try:
            for k, v in self.media_rules.items():
                #SWITCH
                swtch = self.builder.get_object('swtch+{}'.format(k))
                if swtch:
                    widgetid = Gtk.Buildable.get_name(swtch)
                    v = widgetid.split('+')
                    mediaid = v[1]

                    if k == JSON_RULE_USB_MEMORY:
                        ckb = self.builder.get_object('ckb+{}'.format(k))
                        if ckb and ckb.get_active():
                            self.media_rules[mediaid][JSON_RULE_STATE] = JSON_RULE_READONLY
                            continue

                    state = JSON_RULE_ALLOW if swtch.get_active() else JSON_RULE_DISALLOW
                    self.media_rules[mediaid][JSON_RULE_STATE] = state

            #WHITE LIST
            usb_wl = self.read_txtvw('txtvw_usb_whitelist')
            self.media_rules[JSON_RULE_USB_MEMORY][JSON_RULE_USB_SERIALNO] = \
                usb_wl.strip('\n').split('\n')

            bluetooth_wl = self.read_txtvw('txtvw_bluetooth_whitelist')
            self.media_rules[JSON_RULE_BLUETOOTH][JSON_RULE_MAC_ADDRESS] = \
                bluetooth_wl.strip('\n').split('\n')

            usb_network_wl = self.builder.get_object('ent_usb_network_whitelist').get_text()
            self.media_rules[JSON_RULE_USB_NETWORK][JSON_RULE_USB_NETWORK_WHITELIST] = \
                {'busno':usb_network_wl}

            #IPTABLES
            txt_list = self.read_txtvw('txtvw_iptables').split('\n')
            rules_raw = []
            for seq, tl in enumerate(txt_list):
                if tl:
                    rules_raw.append({'seq':str(seq+1), 'cmd':tl})

            self.media_rules[JSON_RULE_NETWORK][JSON_RULE_NETWORK_RULES_RAW] = rules_raw

            #SAVE TO MEMORY
            org_form = {}
            for k, v in self.media_rules.items():
                if len(v) == 1:
                    org_form[k] = v[JSON_RULE_STATE]
                else:
                    org_form[k] = v
            
            #SAVE TO FILE
            TMP_MEDIA_DEFAULT = '/var/tmp/TMP-MEDIA-DEFAULT'
            with open(TMP_MEDIA_DEFAULT, 'w') as f:
                f.write(json.dumps(org_form, indent=4))
            shutil.copy(TMP_MEDIA_DEFAULT, DEFAULT_RULES_PATH)

            self.logging(_('save success'))
        except:
            self.logging(traceback.format_exc())

    def on_menu_apply_activate(self, obj):
        """
        menu > File > apply
        """

        self.on_menu_save_activate(obj)

        try:
            system_bus = dbus.SystemBus()
            bus_object = system_bus.get_object(DBUS_NAME, DBUS_OBJ)
            bus_interface = dbus.Interface(bus_object, dbus_interface=DBUS_IFACE)
            bus_interface.reload('')
            self.logging(_('apply success'))
        except:
            self.logging(traceback.format_exc())
            self.logging(_('save fail'))

    def on_menu_quit_activate(self, obj):
        """
        menu > File > quit
        """

        Gtk.main_quit()

    def on_menu_help_activate(self, obj):
        """
        menu > Help > Help
        """
        os.system("yelp help:grac-editors")

    def on_menu_load_activate(self, obj):
        """
        menu > File > load
        """

        try:
            self.media_rules = self.load_rules(DEFAULT_RULES_PATH)
            self.draw_media(self.media_rules)
            self.logging(_('reset success'))
        except:
            self.logging(traceback.format_exc())
            self.logging(_('reset fail'))
        
    def lang(self):
        """
        under international flag
        """

        #main
        self.builder.get_object('hbar_main').set_title(_('GRAC Editor'))

        self.builder.get_object('lbl_usb_memory').set_label(_('USB Memory'))
        self.builder.get_object('lbl_printer').set_label(_('Printer'))
        self.builder.get_object('lbl_cd_dvd').set_label(_('CD/DVD'))
        self.builder.get_object('lbl_camera').set_label(_('Camera'))
        self.builder.get_object('lbl_sound').set_label(_('Sound'))
        self.builder.get_object('lbl_microphone').set_label(_('Microphone'))
        self.builder.get_object('lbl_wireless').set_label(_('Wireless'))
        self.builder.get_object('lbl_bluetooth').set_label(_('Bluetooth'))
        self.builder.get_object('lbl_keyboard').set_label(_('USB Keyboard'))
        self.builder.get_object('lbl_mouse').set_label(_('USB Mouse'))
        self.builder.get_object('lbl_screen_capture').set_label(_('ScreenCapture'))
        self.builder.get_object('lbl_clipboard').set_label(_('Clipboard'))
        self.builder.get_object('lbl_readonly').set_label(_('readonly'))
        self.builder.get_object('lbl_input_serial').set_label(_('Input serial'))
        self.builder.get_object('lbl_input_mac').set_label(_('Input mac'))
        self.builder.get_object('lbl_input_busno').set_label(_('Input busno'))
        self.builder.get_object('lbl_firewall').set_label(_('Firewall'))
        self.builder.get_object('lbl_first_subtitle').set_label(_('Media Control'))
        self.builder.get_object('lbl_second_subtitle').set_label(_('Device'))

        #menu
        self.builder.get_object('menu_load').set_label(_('_Reset(R)'))
        self.builder.get_object('menu_apply').set_label(_('_Save(S)'))
        self.builder.get_object('menu_quit').set_label(_('_Quit(Q)'))
        self.builder.get_object('menu_help').set_label(_('_Help'))
        self.builder.get_object('menu_remove_user_rule').set_label(_('_Remove User Rule(U)'))

#-----------------------------------------------------------------------
def check_online_account():
    """
    check if login-account is online-account
    """

    import struct
    from pwd import getpwnam

    with open('/var/run/utmp', 'rb') as f:
        fc = memoryview(f.read())

    utmp_fmt = '<ii32s4s32s'
    user_id = '-'

    for i in range(int(len(fc)/384)):
        ut_type, ut_pid, ut_line, ut_id, ut_user = \
            struct.unpack(utmp_fmt, fc[384*i:76+(384*i)])
        ut_line = ut_line.decode('utf8').strip('\00')
        ut_id = ut_id.decode('utf8').strip('\00')

        if ut_type == 7 and ut_id == ':0':
            user_id = ut_user.decode('utf8').strip('\00')

    #check if user_id is an online account
    with open('/etc/passwd') as f:
        pws = f.readlines()

    if user_id == '-':
        return False, 'can not find login-account.'

    #user_id is a local account
    gecos = getpwnam(user_id).pw_gecos.split(',')
    if len(gecos) >= 5 and gecos[4] == 'gooroom-account':
        return False, _('online-account can not use editor.')
    else:
        user_id = '+' + user_id
        return True, ''

#-------------------------------------------------------------------------------
if __name__ == '__main__':

    res, msg = check_online_account()
    if not res:
        md = Gtk.MessageDialog(
            None, 
            0, 
            Gtk.MessageType.WARNING, 
            Gtk.ButtonsType.CLOSE, 
            msg)
        md.run()
        md.destroy()
        sys.exit(1)

    ge = GracEditor()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Gtk.main()

