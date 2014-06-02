# -*- coding: utf-8 -*-

from json import dumps
from kivy.app import App
from kivy.clock import Clock
from kivy.config import ConfigParser
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.stacklayout import StackLayout
from kivy.uix.label import Label
from kivy.uix.settings import SettingsWithNoMenu, SettingString, SettingNumeric
from kivy.uix.switch import Switch

from custom_classes import ScreenWithMenu, Menu

class HomeMenu(Menu):
	pass

class Home(ScreenWithMenu):
	
	devices_screen = ObjectProperty()
	
	def __init__(self, *args, **kwargs):
		super(Home, self).__init__(*args, **kwargs)
		self.app = App.get_running_app()
		self.add_device_popup = AddDevicePopup(self)
		self.devices_list = []
		
	def open_add_device_popup(self):
		self.add_device_popup.open()
	
	def on_enter(self):
		del self.devices_list[:]
		self.devices_screen.clear_widgets()
		
		self.app.send_request(self.build_screen,
							  {'command': 'get_devices'})
		
		Clock.schedule_interval(self.request_screen_update, 2)
	
	def on_leave(self):
		Clock.unschedule(self.request_screen_update)
	
	def build_screen(self, req, result):
		for json_device in result:
			self.add_json_device(json_device)
		self.request_screen_update()
	
	def request_screen_update(self, *args):
		self.app.send_request(self.update_screen,
							  {'command': 'update_devices'})
	
	def update_screen(self, req, result):
		for device_box in self.devices_list:
			for json_device in result:
				if device_box.maj_id == json_device['id']:
					device_box.update(json_device)
	
	def add_json_device(self, json_device):
		new_device_box = DeviceBox(json_device)
		self.devices_list.append(new_device_box)
		self.devices_screen.add_widget(new_device_box)

class DeviceBox(BoxLayout):
	
	nexa_controllers = ['Nexa3ButtonRemote',
						'Nexa2ButtonSwitch']
	
	nexa_sensors = ['NexaOpeningSensor',
					'NexaMovementSensor']
	
	nexa_devices = ['NexaDevice']
	
	def __init__(self, json_device, *args, **kwargs):
		super(DeviceBox, self).__init__(*args, **kwargs)
		
		self.app = App.get_running_app()
		
		print 'building device box'
		print json_device
		print '\n'
		
		self.maj_id = json_device['id']
		self.model = json_device['device_key']
		self.name = json_device['name']
		
		self.orientation = 'vertical'
		self.add_widget(Label(text = self.name,
							  text_size = (self.width-dp(10), 35)))
		
		if self.model in self.nexa_controllers:
			self.switches = []
			for switch in json_device['switches']:
				if switch['state'] != None:	state = switch['state']
				else: state = False
				new_switch = Switch(id = switch['id'], active = state, disabled = True) 
				self.switches.append(new_switch)
				self.add_widget(new_switch)
		elif self.model in self.nexa_sensors:
			self.last_activated = Label(text = json_device['last_activated'],
									    size_hint = (None, 1),
									    text_size = (self.width-dp(10), 100),
									    pos_hint = {'center_x': 0.5})
			self.add_widget(self.last_activated)
		elif self.model in self.nexa_devices:
			self.switch = Switch(id = json_device['id'])
			self.switch.bind(active = self.user_action)
			self.add_widget(self.switch)
		
	def update(self, json_update):
		
		if self.model in self.nexa_controllers:
			for switch in json_update['switches']:
				for my_switch in self.switches:
					if switch['id'] == my_switch.id:
						if switch['state'] != None:
							my_switch.active = switch['state']
		elif self.model in self.nexa_sensors:
			self.last_activated.text = json_update['last_activated']
		elif self.model in self.nexa_devices:
			if json_update['state'] != None:
				self.switch.unbind(active = self.user_action)
				self.switch.active = json_update['state']
				self.switch.bind(active = self.user_action)

	def user_action(self, instance, value):
		
		print 'sending action request'
		print {'command': 'device_action',
			   'model': self.model,
			   'id': instance.id}
		
		self.app.send_request(None,
							  {'command': 'device_action',
							   'model': self.model,
							   'id': instance.id})

class AddDevicePopup(Popup):
	
	scrollview = ObjectProperty()
	purpose = StringProperty('')
	
	def __init__(self, home_screen, *args, **kwargs):
		super(AddDevicePopup, self).__init__(*args, **kwargs)
		
		self.home_screen = home_screen
		self.title = 'Add a device'
		self.device_id = None
		self.device_model_id = None
		self.scheduled = []
		
		self.syncview = SyncView(self)
		self.checkview = CheckView(self)
		self.settingsview = SettingsView(self)
		self.listview = ListView(self)
		self.syncview = SyncView(self)
		self.autoaddview = AutoAddView(self)
		
	def on_open(self):
		self.scheduled = []
		self.state = 'list'
		self.content = self.listview
		self.content.on_enter()
	
	def on_dismiss(self):
		for function in self.scheduled:
			Clock.unschedule(function)
		self.home_screen.on_enter()
		
	def next_view(self, *args):
		
		next_view = {'sync_settings' :	{'state': 'sync_waiting',
										 'view': self.syncview},
					 'sync_waiting' :	{'state': 'sync_check',
										 'view': self.checkview},
					 'sync_check' :		{'state': None,
									 	 'view': None},
					 'auto_add' :		{'state': 'auto_settings',
								   		 'view': self.settingsview},
					 'auto_settings' :	{'state': None,
									     'view': None}}
		
		if next_view[self.state]['state'] != None:
			self.content = next_view[self.state]['view']
			self.content.on_enter()
			self.state = next_view[self.state]['state']
		else:
			self.dismiss()
	
	def previous_view(self, *args):
		
		previous_view = {'sync_settings' :	{'state': 'list',
										 	 'view': self.listview},
						 'sync_waiting' :	{'state': 'sync_settings',
											 'view': self.settingsview},
						 'sync_check' :		{'state': 'sync_waiting',
										 	 'view': self.syncview},
						 'auto_add' :		{'state': 'list',
									   		 'view': self.listview},
						 'auto_settings' :	{'state': 'auto_add',
										     'view': self.autoaddview}}
		
		if previous_view[self.state]['state'] != None:
			self.content = previous_view[self.state]['view']
			self.content.on_enter()
			self.state = previous_view[self.state]['state']
		else:
			self.dismiss()

class ListView(StackLayout):
	
	def __init__(self, popup, *args, **kwargs):
		super(ListView, self).__init__(*args, **kwargs)

		self.app = App.get_running_app()
		self.popup = popup

	def on_enter(self):
		self.clear_widgets()
		self.app.send_request(self.build_view,
				  			  {'command': 'get_device_models'})
	
	def build_view(self, req, result):
		
		for element in result:
			print element['name'], element['id']
			self.add_widget(Button(text = element['name'],
								   id = element['id'],
								   on_release = self.choice_made,
								   size_hint = (1, None),
								   height = '30dp',
								   pos_hint= {'top': 1}))
	
	def choice_made(self, button):

		self.popup.device_model_id = button.id

		self.app.send_request(self.start_adding_process,
							  {'command': 'start_adding_process',
							   'device_model_id': button.id})

	def start_adding_process(self, req, result):
		""" If the device's adding_type is sync then :
			1) écran de settings
			2) écran qui invite à synchroniser
			3) écran de vérification de synchronisation
			
			Otherwise, if the device's adding_type is auto_add:
			1) écran qui invite à initier les actions nécessaires (appui sur un bouton...)
			2) écran de settings
		"""
		
		if result['adding_type'] == 'sync':
			self.popup.device_id = result['device_id']	
			self.popup.state = 'sync_settings'
			self.popup.content = self.popup.settingsview
			self.popup.content.on_enter()
		elif result['adding_type'] == 'auto':
			self.popup.state = 'auto_add'
			self.popup.content = self.popup.autoaddview
			self.popup.content.on_enter()
		print self.popup.state
		
class SettingsView(BoxLayout):
	# Il y a juste à récupérer les settings comme d'hab et les afficher en utilsant les Settings de Kivy
	# Ajouter deux bouton 'Go back' et 'Continue' en bas
	
	popup = ObjectProperty()
	
	def __init__(self, popup, *args, **kwargs):
		super(SettingsView, self).__init__(*args, **kwargs)
		
		self.popup = popup
		self.app = App.get_running_app()
		self.orientation = 'vertical'
		
	def on_enter(self):
		self.clear_widgets()
		self.app.send_request(self.build_settings,
							  {'command': 'get_device_settings',
							   'device_id': self.popup.device_id})
	
	def build_settings(self, req, result):
		
		self.settings = None
		self.settings = SettingsWithNoMenu()
		self.settings.on_config_change = self.on_config_change
		self.settings.register_type('string_long', SettingString)
		self.settings.register_type('num_int', SettingNumeric)
		self.settings.register_type('num', SettingNumeric)
		
		config = ConfigParser()
		print result['settings']
		config.setdefaults(self.popup.device_id, result['settings'])
		self.settings.add_json_panel(result['name'], config, data=dumps(result['settings_format']))		
		self.add_widget(self.settings)
		
		buttons = BoxLayout(orientation = 'horizontal')
		buttons.add_widget(Button(text = 'Previous',
								  on_release = self.popup.previous_view,
								  height = '50dp'))
		buttons.add_widget(Button(text = 'Next',
								  on_release = self.popup.next_view,
								  height = '50dp'))
		self.add_widget(buttons)
	
	def on_config_change(self, config, section, key, value):
		
		self.app.send_request(None,
							  {'command': 'set_device',
							   'device_id': self.popup.device_id,
							   'settings': {key: value}})

class SyncView(BoxLayout):
	# Il faut juste afficher les instructions de synchronisation ainsi que deux boutons 'Go back' et 'Continue'
	def __init__(self, popup, *args, **kwargs):
		super(SyncView, self).__init__(*args, **kwargs)
		
		self.app = App.get_running_app()
		self.popup = popup
		self.orientation = 'vertical'
		self.padding = ['10dp', '10dp', '10dp', '10dp']		
		
	def on_enter(self):
		self.clear_widgets()
		self.app.send_request(self.build_view,
							  {'command': 'get_sync_instructions',
							   'device_model_id': self.popup.device_model_id})
	
	def build_view(self, req, result):
		
		self.add_widget(Label(text = result['instructions'],
							  size_hint = (None, 1),
							  text_size = (self.width-dp(20), 100),
							  pos_hint = {'center_x': 0.5}))
		
		self.add_widget(Button(text = 'Sync',
							   on_release = self.send_sync_signal,
							   height = '50dp'))
		
		buttons = BoxLayout(orientation = 'horizontal')
		buttons.add_widget(Button(text = 'Previous',
								  on_release = self.popup.previous_view,
								  height = '50dp'))
		buttons.add_widget(Button(text = 'Next',
								  on_release = self.popup.next_view,
								  height = '50dp'))
		self.add_widget(buttons)
	
	def send_sync_signal(self, *args):
		
		self.app.send_request(None,
							  {'command': 'send_sync_signal',
							   'device_id': self.popup.device_id})
		
class CheckView(BoxLayout):
	# Il faut afficher :
	# 1) un texte explicatif qui dit que c'est l'écran de vérification 
	# 2) la device comme elle sera affichée sur le Home Screen
	# ainsi que deux boutons 'Go back' et 'Continue'
	
	def __init__(self, popup, *args, **kwargs):
		super(CheckView, self).__init__(*args, **kwargs)

		self.app = App.get_running_app()
		self.orientation = 'vertical'
		self.padding = ['10dp', '10dp', '10dp', '10dp']		
		self.spacing = '20dp' 
		
	def on_enter(self):
		
		self.clear_widgets()
		self.app.send_request(self.build_view,
							  {'command': 'get_devices',
							   'device_ids': [self.popup.device_id]})
		
	def build_view(self, req, result):

		print 'building check view'
		check_text = 	'On this screen, you can check whether or not your device has been successfully synced. If the device seems functional, then continue. Otherwise, go back to the previous screen and start again the syncing process.'

		self.add_widget(Label(text = check_text,
							  size_hint = (None, 1),
							  text_size = (self.width-dp(20), 100),
							  pos_hint = {'center_x': 0.5}))
		
		for device in result:
			if device['id'] == self.popup.device_id:
				self.add_widget(DeviceBox(device, pos_hint = {'center_x': 0.5}))
		
		buttons = BoxLayout(orientation = 'horizontal')
		buttons.add_widget(Button(text = 'Previous',
								  on_release = self.popup.previous_view,
								  height = '50dp'))
		buttons.add_widget(Button(text = 'Next',
								  on_release = self.popup.next_view,
								  height = '50dp'))
		self.add_widget(buttons)

class AutoAddView(BoxLayout):
	# En entrant, il faut faire une requête pour lancer l'auto-detect de ce type de devices
	# Il faut planifier une requête pour vérifier si on a récupéré le bon type de device toutes les 2-3 secondes
	# En sortant, quand la device a été détectée, il faut bien arrêter le process de détection auto
	popup = ObjectProperty()
	
	def __init__(self, popup, *args, **kwargs):
		super(AutoAddView, self).__init__(*args, **kwargs)
		
		self.app = App.get_running_app()
		self.popup = popup
		
	def on_enter(self):
		self.clear_widgets()
		self.app.send_request(self.build_view,
							  {'command': 'get_auto_add_instructions',
							   'device_model_id': self.popup.device_model_id})
	
	def build_view(self, req, result):
		
		Clock.schedule_interval(self.send_check_request, 2)
		self.popup.scheduled.append(self.send_check_request)
		
		self.orientation = 'vertical'
		self.padding = ['10dp', '10dp', '10dp', '10dp']		
		
		self.add_widget(Label(text = result['instructions'],
							  size_hint = (None, 1),
							  text_size = (self.width-dp(20), 100),
							  pos_hint = {'center_x': 0.5}))
		
		buttons = BoxLayout(orientation = 'horizontal')
		buttons.add_widget(Button(text = 'Previous',
								  on_release = self.popup.previous_view,
								  height = '50dp'))
		self.add_widget(buttons)
		
	def send_check_request(self, *args):
		
		self.app.send_request(self.check_if_detected,
							  {'command': 'check_if_device_detected',
							   'device_model_id': self.popup.device_model_id})
		
	def check_if_detected(self, req, result):
		
		if result.has_key('detected'):
			if result['detected']:
				self.popup.device_id = result['device_id']
				Clock.unschedule(self.send_check_request)
				self.popup.next_view()