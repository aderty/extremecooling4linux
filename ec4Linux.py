#!/usr/bin/python3
import sys, time, os
import portio
import logging
import subprocess
import gettext
import locale
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GLib

# create logger
logger = logging.getLogger('batteryoptimizer')
logging.basicConfig(level=logging.INFO)
APP ='batteryoptimizer'


class Error(Exception):
    pass


class TimeOutEcWait(Error):

    def __init__(self, message):
        self.expresion = message


class EcReadException(Error):

    def __init__(self, message):
        self.expresion = message


class EcWriteException(Error):

    def __init__(self, message):
        self.expresion = message


class NoSupportedExtremeCoolingException(Error):

    def __init__(self, message):
        self.expresion = message


class NonDetectedExtremeCoolingException(Error):

    def __init__(self, message):
        self.expresion = message


class DmiDecodeNotFoundException(Error):
    def __init__(self, message):
        self.message = message


class DialogUI(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Extreme Cooling")

    def create_dialog(self, message, secondary_message, buttons_type,gtk_message_type):
        dialog = Gtk.MessageDialog(parent = self, modal=True, message_type = gtk_message_type, buttons = buttons_type, text = message)
        dialog.format_secondary_text(secondary_message)
        dialog.run()
        dialog.destroy()


class DmiReader:

    sys_dmi_path = "/sys/devices/virtual/dmi/id"

    def read_bios_version(self):
        return self._read_from_sys("bios_version")

    def read_bios_date(self):
        return self._read_from_sys("bios_date")

    def read_bios_vendor(self):
        return self._read_from_sys("bios_vendor")

    def read_product_name(self):
        return self._read_from_sys("product_name")

    def read_product_version(self):
        return self._read_from_sys("product_version")

    def read_sys_vendor(self):
        return self._read_from_sys("sys_vendor")

    def read_chassis_type(self):
        return self._read_from_sys("chassis_type")

    def read_board_vendor(self):
        return self._read_from_sys("board_vendor")

    def read_board_name(self):
        return self._read_from_sys("board_name")

    def read_board_version(self):
        return self._read_from_sys("board_version")

    def _read_from_sys(self, parameter):
        property_value = None
        try:
            with open(os.path.join(self.sys_dmi_path, parameter), 'r') as property:
                property_value = str(property.readline())
                if property_value is not None:
                    property_value=property_value.replace('\n', '')
        except Exception:
            logger.info('Error reading dmi sys information %s' % parameter)
        return property_value

class Util:

    directory_name="extremecooling4linux"

    def elevate(self):
        if os.getuid() == 0:
            return
        else:
            try:
                command=os.path.dirname(__file__)+"/exec4Linux.sh"
                result = subprocess.run([command])
                if result != 0:
                    sys.exit(1)
            except Exception as e:
                logger.error(e)

    def config_path_exists(self):
        path=self.get_config_path()
        if path is not None:
            return os.path.exists(self.get_config_path())
        else:
            return False

    def get_config_path(self):
        if os.path.exists(os.path.join(GLib.get_user_config_dir(), self.directory_name)):
            return os.path.join(GLib.get_user_config_dir(),  self.directory_name)
        else:
            logger.info("there is not a configuration directory")
            return None

    def create_config_path(self):
        if not self.config_path_exists():
            os.makedirs(os.path.join(GLib.get_user_config_dir(), self.directory_name))

    def get_data_path(self):
        if getattr(sys, 'frozen', False):
            base_folder = sys._MEIPASS
            logger.info("base_folder %s" % base_folder)
            return base_folder + "/usr/share/" + self.directory_name + "/data"
        elif os.path.exists(os.path.dirname(__file__) + "/usr/share/" + self.directory_name + "/data"):
            return os.path.dirname(__file__) + "/usr/share/" + self.directory_name + "/data"
        elif os.path.exists(os.path.dirname(__file__) + "/data"):
            return os.path.dirname(__file__)+ "/data"
        elif os.path.exists("/usr/share/" + self.directory_name + "/data"):
            return "/usr/share/" + self.directory_name + "/data"
        else:
            logger.info("there is not a data directory")
            return None

    def get_po_path(self):
        if getattr(sys, 'frozen', False):
            base_folder = sys._MEIPASS
            logger.info("base_folder %s" % base_folder)
            return base_folder + "/usr/share/locale/"
        elif os.path.exists(os.path.dirname(__file__) + "usr/share/locale/"):
            return os.path.dirname(__file__) + "/usr/share/locale/"
        elif os.path.exists(os.path.dirname(__file__) + "/locale/"):
            return os.path.dirname(__file__) + "/locale/"
        else:
            return "/usr/share/locale/"

    def get_glade_files_path(self):
        return os.path.join(self.get_data_path(), "glade_files")


class EmbeddedController:

    #Embedded Controller Command, EC_SC
    EC_SC = 0x66
    #Embedded Controller Data
    EC_DATA = 0x62
    #Input Buffer Full (IBF) flag, Input Buffer is full 1, Input Buffer is empty 0
    IBF = 1
    #Output Buffer Full (OBF) flag, Output buffer is full 1, Output buffer is empty 0
    OBF = 0
    #Read Embedded Controller(RD_EC)
    RD_EC = 0x80
    #Write Embedded Controller(WR_EC)
    WR_EC = 0x81
    # Query Embedded Controller(QR_EC)
    QR_EC = 0x84
    # Extreme Cooling Register
    EXTREME_COOLING_REGISTER = 0xD7
    #ACTIVATE
    ACTIVATE_EXTREME_COOLING = 0xBC
    #DEACTIVATE
    DEACTIVATE_EXTREME_COOLING = 0xE4
    #MEDIUM
    MEDIUM_EXTREME_COOLING = 0xD0

    def inicializate(self):
        error = False
        try:
            for register in [self.EC_DATA, self.EC_SC]:
                status = portio.ioperm(register, 1, 1)
                if status:
                    error = True
                    logger.error('ioperm:', os.strerror(status))
                else:
                    logger.info('acces to :'+ str(hex(register)))
            if error:
                return False
            else:
                return True
        except TypeError as te:
            logger.error(te)
            return False

    def ec_wait(self, port, flag, value):
        logger.info("ec_wait")
        condition=False
        for i in range(100):
            data = portio.inb(port)
            if ((data >> flag) & 0x1) == value:
                condition = True
                break
            time.sleep(0.001)
        if not condition:
            logger.warning("timeout in ec_wait")
            raise TimeOutEcWait("timeout in ec_wait")
        else:
            logger.info("ec_wait correct")

    def ec_read(self, port):
        try:
            self.ec_wait(self.EC_SC, self.IBF, 0)
            portio.outb(self.RD_EC, self.EC_SC)
            self.ec_wait(self.EC_SC, self.IBF, 0)
            portio.outb(port, self.EC_DATA)
            self.ec_wait(self.EC_SC, self.OBF, 1)
            result = portio.inb(self.EC_DATA)
            return result
        except TimeOutEcWait as terror:
            logger.error(terror)
            raise EcReadException("error reading port" + str(hex(port)))

    def ec_write(self, port, value):
        try:
            self.ec_wait(self.EC_SC, self.IBF, 0)
            portio.outb(self.WR_EC, self.EC_SC)
            self.ec_wait(self.EC_SC, self.IBF, 0)
            portio.outb(port, self.EC_DATA)
            self.ec_wait(self.EC_SC, self.IBF, 0)
            portio.outb(value, self.EC_DATA)
            self.ec_wait(self.EC_SC, self.IBF, 0)
        except TimeOutEcWait as terror:
            logger.error(terror)
            raise EcWriteException("error write port" + str(hex(port)))

    def activate_extreme_cooling(self):
        logger.info("activate_extreme_cooling")
        try:
            self.detect_extreme_cooling_supported()
            self.ec_write(self.EXTREME_COOLING_REGISTER, self.ACTIVATE_EXTREME_COOLING)
        except EcWriteException:
            logger.error("Error writen ec, activate extreme cooling failed")
            raise NoSupportedExtremeCoolingException("Error trying to active extreme cooling. Your laptop does not support extreme cooling.")

    def is_extreme_cooling_activate(self):
        try:
            val = self.ec_read(self.EXTREME_COOLING_REGISTER)
            logger.info("is_extreme_cooling_activate value register " + str(hex(val)))
            if hex(val) == hex(self.ACTIVATE_EXTREME_COOLING):
                return True
            else:
                return False
        except EcReadException:
            logger.error("Error reading ec, getting  extreme cooling status failed")
            return False

    def deactivate_extreme_cooling(self):
        logger.info("deactivate_extreme_cooling")
        try:
            self.detect_extreme_cooling_supported()
            self.ec_write(self.EXTREME_COOLING_REGISTER, self.DEACTIVATE_EXTREME_COOLING)
        except EcWriteException:
            logger.error("Error writen ec, deactivate extreme cooling failed")
            raise NoSupportedExtremeCoolingException("Error trying to deactivate extreme cooling. Your laptop does not support extreme cooling.")

    def detect_extreme_cooling_supported(self):
        return True;
        try:
            logger.info("trying to detect extreme cooling support")
            manufacturer = DmiReader().read_sys_vendor()
            chassis = DmiReader().read_chassis_type()
            product_name = DmiReader().read_product_name()
            product_version = DmiReader().read_product_version()
            logger.info("system_manufacturer %s" % manufacturer)
            logger.info("product_name %s" % product_name)
            logger.info("product_version %s" % product_version)
            logger.info("chassis_type %s" % chassis)
            if 'LENOVO' != manufacturer or chassis not in ['9', '10', '14'] :
                logger.info("Extreme cooling is only supported in LENOVO laptops, there is not support in %s" % manufacturer)
                raise NoSupportedExtremeCoolingException("Your laptop %s does not support extreme cooling." % manufacturer)
            val = self.ec_read(self.EXTREME_COOLING_REGISTER)
            logger.info("is_extreme_cooling_activate value register %s " % hex(val))
            if  hex(val) == hex(self.ACTIVATE_EXTREME_COOLING) or hex(val) == hex(self.DEACTIVATE_EXTREME_COOLING) or hex(val) == hex(0x80):
                logger.info("Extreme cooling could be supported, current value in extreme cooling register is %s " % hex(val))
            else:
                logger.info("Extreme cooling not supported, current value in extreme cooling register not valid %s " % hex(val))
                raise NoSupportedExtremeCoolingException("Your laptop does not support extreme cooling.")
        except EcReadException:
            logger.error("Exception extreme cooling not detected")


class MainUIPage:

    def __init__(self, builder, ec, util):
        self.builder = builder
        self.window = None
        self.util = util
        self.ec = ec
        self.enable_ec_switch_button = self.builder.get_object("id_enable_extreme_cooling_switch")

    def load_window(self):
        self.enable_ec_switch_button.connect("notify::active", self.on_extreme_cooling_switch_activate)
        if os.getuid() == 0:
            self.ec.inicializate()
            try:
                self.ec.detect_extreme_cooling_supported()
            except NoSupportedExtremeCoolingException:
                self.enable_ec_switch_button.set_sensitive(False)
                dialog = DialogUI()
                dialog.create_dialog(_("Error"), _(
                    "Your laptop does not support Extreme Cooling fan mode. Only some Lenovo laptops supports this feature."),
                                     Gtk.ButtonsType.OK, Gtk.MessageType.ERROR)
            self.enable_ec_switch_button.set_active(self.ec.is_extreme_cooling_activate())
        else:
            if getattr(sys, '_MEIPASS', ''):
                self.enable_ec_switch_button.set_sensitive(False)
                dialog = DialogUI()
                dialog.create_dialog(_("User does not have enough privileges."), _("BatteryOptimizer needs root privileges to enable/disable extreme cooling. Please, execute BatteryOptimizer with sudo."),
                                     Gtk.ButtonsType.OK, Gtk.MessageType.INFO)
            logger.warning("You do not have root permissions to disable Extreme Cooling")



    def on_extreme_cooling_switch_activate(self, button, active):
        logger.info("on_extreme_cooling_switch_activate")
        if button.get_active():
            if os.getuid() == 0:
                try:
                    logger.info("activate")
                    self.ec.activate_extreme_cooling()
                except NoSupportedExtremeCoolingException:
                    dialog = DialogUI()
                    dialog.create_dialog(_("Error"), _("Your laptop does not support Extreme Cooling fan mode. Only some Lenovo laptops supports this feature."),Gtk.ButtonsType.OK, Gtk.MessageType.ERROR)
            else:
                logger.warning("You do not have root permissions to enable Extreme Cooling")
                try:
                    execute = os.path.join(os.path.abspath(os.path.dirname(__file__)), sys.argv[0])
                    logger.info(execute)
                    result = subprocess.run(["pkexec", execute, "enable"], check=True)
                except subprocess.CalledProcessError as e:
                    logger.error(e)
                    dialog = DialogUI()
                    dialog.create_dialog(_("Error"), _("Enable extreme cooling failed"), Gtk.ButtonsType.OK, Gtk.MessageType.ERROR)
        else:
            if os.getuid() == 0:
                try:
                    logger.info("deactivate")
                    self.ec.deactivate_extreme_cooling()
                except NoSupportedExtremeCoolingException:
                    dialog = DialogUI()
                    dialog.create_dialog(_("Error"), _("Your laptop does not support Extreme Cooling fan mode. Only some Lenovo laptops supports this feature."),
                            Gtk.ButtonsType.OK,Gtk.MessageType.ERROR)
            else:
                logger.warning("You do not have root permissions to disable Extreme Cooling")
                try:
                    execute = os.path.join(os.path.abspath(os.path.dirname(__file__)), sys.argv[0])
                    logger.info(execute)
                    result = subprocess.run(["pkexec", execute, "disable"], check = True)
                except subprocess.CalledProcessError as e:
                    logger.error(e)
                    dialog = DialogUI()
                    dialog.create_dialog(_("Error"), _("Disable extreme cooling failed"), Gtk.ButtonsType.OK,Gtk.MessageType.ERROR)


class SystemUIPage:

    def __init__(self, builder, ec, util):
        self.builder = builder
        self.util = util
        self.ec = ec
        self.bios_version_value_label = self.builder.get_object("id_bios_version_value")
        self.bios_vendor_value_label = self.builder.get_object("id_bios_vendor_value")
        self.bios_release_date_value_label = self.builder.get_object("id_bios_release_date_value")
        self.product_version_value_label = self.builder.get_object("id_product_version_value")
        self.product_name_value_label = self.builder.get_object("id_product_name_value")
        self.sys_name_vendor_label = self.builder.get_object("id_sys_vendor_value")
        self.board_name_value_label = self.builder.get_object("id_board_name_value")
        self.board_version_value_label = self.builder.get_object("id_board_version_value")
        self.board_vendor_value_label = self.builder.get_object("id_board_vendor_value")
        self.list_box_bios = self.builder.get_object("id_list_box_bios")

    def load_window(self):
        self.bios_version_value_label.set_text(self.set_label_value(DmiReader().read_bios_version()))
        self.bios_vendor_value_label.set_text(self.set_label_value(DmiReader().read_bios_vendor()))
        self.bios_release_date_value_label.set_text(self.set_label_value(DmiReader().read_bios_date()))
        self.product_version_value_label.set_text(self.set_label_value(DmiReader().read_product_version()))
        self.product_name_value_label.set_text(self.set_label_value(DmiReader().read_product_name()))
        self.sys_name_vendor_label.set_text(self.set_label_value(DmiReader().read_sys_vendor()))
        self.board_name_value_label.set_text(self.set_label_value(DmiReader().read_board_name()))
        self.board_version_value_label.set_text(self.set_label_value(DmiReader().read_board_version()))
        self.board_vendor_value_label.set_text(self.set_label_value(DmiReader().read_board_vendor()))

    def set_label_value(self,value):
        if value is not None:
            return value
        else:
            return ''


class MainUI:

    def __init__(self, builder, ec, util):
        self.builder = builder
        self.window = None
        self.util = util
        self.ec = ec
        self.glade_file = os.path.join(self.util.get_glade_files_path(), "mainui.glade")
        self.builder.add_from_file(self.glade_file)
        self.main_ui_page = MainUIPage(builder, self.ec, self.util)
        self.system_ui_page = SystemUIPage(builder, self.ec, self.util)

    def load_window(self):
        self.window = self.builder.get_object("id_main_window")
        self.builder.connect_signals(self)
        self.main_ui_page.load_window()
        self.system_ui_page.load_window()
        self.window.connect('destroy', Gtk.main_quit)
        self.window.show_all()
        Gtk.main()

    def on_about_clicked(self, button):
        logger.info("on_about_clicked")
        self.builder.get_object("id_about_dialog").run()
        self.builder.get_object("id_about_dialog").hide()

    def on_mainWindow_destroy(self, *args):
        Gtk.main_quit()

    def onDestroy(self, *args):
        Gtk.main_quit()


class App:

    def __init__(self):
        self.util = Util()
        self.main_program = None
        self.ec = EmbeddedController()

    def pre(self):
        self.util.create_config_path()
        logger.info(self.util.get_config_path())
        file_handler = logging.FileHandler(os.path.join(self.util.get_config_path(), 'batteryoptimizer.log'))
        file_handler.setLevel(level=logging.DEBUG)
        logger.addHandler(file_handler)
        logger.info(os.getcwd())
        logger.info("starting program")

    def run_main_ui(self):
        builder = Gtk.Builder()
        builder.set_translation_domain(APP)
        self.main_program = MainUI(builder, self.ec, self.util)
        self.main_program.load_window()

    def execute(self):
        self.pre()
        if os.getuid() == 0:
            logger.info("Root user detected")
        else:
            logger.info("You do not have root permissions")
            #self.util.elevate()
        self.run_main_ui()


if __name__ == '__main__':
    if getattr(sys, '_MEIPASS', ''):
        logger.info('running BatteryOptimizer as PyInstaller bundle')
    else:
        logger.info('running BatteryOptimizer in a normal Python process')
    app = App()
    util = Util()
    LOCALE_DIR = util.get_po_path()
    logger.info(LOCALE_DIR)
    locale.setlocale(locale.LC_ALL, '')
    locale.bindtextdomain(APP, LOCALE_DIR)
    gettext.bindtextdomain(APP, LOCALE_DIR)
    gettext.textdomain(APP)
    _ = gettext.gettext
    try:
        arg1 = sys.argv[1]
        logger.info('running BatteryOptimizer as a command line program')
        if os.getuid() == 0:
            app.ec.inicializate()
            try:
                if arg1 == "enable":
                    app.ec.activate_extreme_cooling()
                elif arg1 == "disable":
                    app.ec.deactivate_extreme_cooling()
                elif arg1 == "check":
                    app.ec.detect_extreme_cooling_supported()
                elif arg1 == "status":
                    logger.info(app.ec.is_extreme_cooling_activate())
                elif arg1 == "change-state":
                    if app.ec.is_extreme_cooling_activate():
                        app.ec.deactivate_extreme_cooling()
                    else:
                        app.ec.activate_extreme_cooling()
                else:
                    logger.info("enable, disable, check, status, and change-state are the only valid arguments for BatteryOptimizer")
            except NoSupportedExtremeCoolingException as e:
                logger.error(e)
        else:
            logger.info("You don't have permissions to execute BatteryOptimizer")
    except IndexError:
        logger.info('running BatteryOptimizer as gui program')
        app.execute()

