from blueman.Functions import *
import pickle
import base64
from blueman.Service import Service
from blueman.main.Config import Config
from blueman.Sdp import parse_sdp_xml, sdp_save
from blueman.main.PluginManager import StopException
from blueman.plugins.AppletPlugin import AppletPlugin
from blueman.main.applet.BluezAgent import AdapterAgent

from blueman.bluez.Device import Device as BluezDevice
from blueman.main.Device import Device
from blueman.main.applet.BluezAgent import TempAgent
from blueman.bluez.Adapter import Adapter

from gi.repository import GObject
from gi.repository import Gtk
import dbus


class DBusService(AppletPlugin):
    __depends__ = ["StatusIcon"]
    __unloadable__ = False
    __description__ = _("Provides DBus API for other Blueman components")
    __author__ = "Walmis"

    def on_load(self, applet):
        self.Applet = applet

        AppletPlugin.add_method(self.on_rfcomm_connected)
        AppletPlugin.add_method(self.on_rfcomm_disconnect)
        AppletPlugin.add_method(self.rfcomm_connect_handler)
        AppletPlugin.add_method(self.service_connect_handler)
        AppletPlugin.add_method(self.service_disconnect_handler)
        AppletPlugin.add_method(self.on_device_disconnect)

        self.add_dbus_method(self.connect_service, in_signature="os", async_callbacks=("ok", "err"))
        self.add_dbus_method(self.disconnect_service, in_signature="oss", async_callbacks=("ok", "err"))
        self.add_dbus_method(self.CreateDevice, in_signature="ssbu", async_callbacks=("_ok", "err"))
        self.add_dbus_method(self.CancelDeviceCreation, in_signature="ss", async_callbacks=("ok", "err"))
        self.add_dbus_method(self.RefreshServices, in_signature="s", out_signature="", async_callbacks=("ok", "err"))

        self.add_dbus_method(self.QueryPlugins, in_signature="", out_signature="as")
        self.add_dbus_method(self.QueryAvailablePlugins, in_signature="", out_signature="as")
        self.add_dbus_method(self.SetPluginConfig, in_signature="sb", out_signature="")
        self.add_dbus_method(self.DisconnectDevice, in_signature="o", out_signature="", async_callbacks=("ok", "err"))

    def RefreshServices(self, path, ok, err):
        # BlueZ 4 only!
        device = Device(path)

        def reply(svcs):
            try:
                records = parse_sdp_xml(svcs)
                sdp_save(device.Address, records)
            except:
                pass
            ok()

        device.get_interface().DiscoverServices("", reply_handler=reply, error_handler=err)

    def QueryPlugins(self):
        return self.Applet.Plugins.GetLoaded()

    def DisconnectDevice(self, obj_path, ok, err):
        dev = Device(obj_path)

        self.Applet.Plugins.Run("on_device_disconnect", dev)

        def on_timeout():
            dev.Disconnect(reply_handler=ok, error_handler=err)

        GObject.timeout_add(1000, on_timeout)

    def on_device_disconnect(self, device):
        pass

    def QueryAvailablePlugins(self):
        return self.Applet.Plugins.GetClasses()

    def SetPluginConfig(self, plugin, value):
        self.Applet.Plugins.SetConfig(plugin, value)

    def connect_service(self, object_path, uuid, ok, err):
        service = Device(object_path).get_service(uuid)

        try:
            self.Applet.Plugins.RecentConns
        except KeyError:
            dprint("RecentConns plugin is unavailable")
        else:
            self.Applet.Plugins.RecentConns.notify(service)

        if service.group == 'serial':
            def reply(rfcomm):
                self.Applet.Plugins.Run("on_rfcomm_connected", service, rfcomm)
                ok(rfcomm)

            rets = self.Applet.Plugins.Run("rfcomm_connect_handler", service, reply, err)
            if True in rets:
                pass
            else:
                dprint("No handler registered")
                err(dbus.DBusException(
                    "Service not supported\nPossibly the plugin that handles this service is not loaded"))
        else:
            def cb(_inst, ret):
                if ret:
                    raise StopException

            if not self.Applet.Plugins.RunEx("service_connect_handler", cb, service, ok, err):
                service.connect(reply_handler=ok, error_handler=err)

    def disconnect_service(self, object_path, uuid, port, ok, err):
        service = Device(object_path).get_service(uuid)

        if service.group == 'serial':
            service.disconnect(port)

            self.Applet.Plugins.Run("on_rfcomm_disconnect", port)

            dprint("Disonnecting rfcomm device")
        else:

            def cb(_inst, ret):
                if ret:
                    raise StopException

            if not self.Applet.Plugins.RunEx("service_disconnect_handler", cb, service, ok, err):
                service.disconnect(reply_handler=ok, error_handler=err)

    def service_connect_handler(self, service, ok, err):
        pass

    def service_disconnect_handler(self, service, ok, err):
        pass

    def CreateDevice(self, adapter_path, address, pair, time, _ok, err):
        # BlueZ 4 only!
        def ok(device):
            path = device.get_object_path()
            _ok(path)
            self.RefreshServices(path, (lambda *args: None), (lambda *args: None))

        if self.Applet.Manager:
            adapter = Adapter(adapter_path)

            if pair:
                agent_path = "/org/blueman/agent/temp/" + address.replace(":", "")
                agent = TempAgent(self.Applet.Plugins.StatusIcon, agent_path, time)
                adapter.create_paired_device(address, agent_path, "DisplayYesNo", error_handler=err,
                                             reply_handler=ok, timeout=120)

            else:
                adapter.create_device(address, error_handler=err, reply_handler=ok, timeout=120)

        else:
            err()

    def CancelDeviceCreation(self, adapter_path, address, ok, err):
        # BlueZ 4 only!
        if self.Applet.Manager:
            adapter = Adapter(adapter_path)

            adapter.get_interface().CancelDeviceCreation(address, error_handler=err, reply_handler=ok)

        else:
            err()

    def rfcomm_connect_handler(self, service, reply_handler, error_handler):
        return False

    def on_rfcomm_connected(self, service, port):
        pass

    def on_rfcomm_disconnect(self, port):
        pass
