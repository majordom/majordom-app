# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.screenmanager import (ScreenManager,
									SlideTransition,
									WipeTransition)
from kivy.uix.anchorlayout import AnchorLayout
								
from screens.login import Login, LoginMenu
from screens.home import Home, HomeMenu
from screens.scenarios import Scenarios, ScenariosMenu, NewScenario, NewScenarioMenu
from kivy.uix.settings import SettingsWithSidebar, SettingString, SettingNumeric
from kivy.network.urlrequest import UrlRequest
from kivy.config import ConfigParser

from json import dumps
from functools import partial

class MenuManager(ScreenManager):
	pass

class Majordom(App):
	
	server = StringProperty('')
	body = ObjectProperty(ScreenManager(transition=SlideTransition(), pos_hint = {'top': 1}))
	menu = ObjectProperty(MenuManager(transition=WipeTransition()))

	def build(self):
		Builder.load_file('screens/login.kv')
		Builder.load_file('screens/home.kv')
		Builder.load_file('screens/scenarios.kv')
		Builder.load_file('main.kv')
		
		self.body.add_widget(Login(LoginMenu, 'loginmenu', None, name = 'login'))
		self.body.add_widget(Home(HomeMenu, 'homemenu', None, name = 'home'))
		self.body.add_widget(Scenarios(ScenariosMenu, 'scenariosmenu', 'home', name = 'scenarios'))
		self.body.add_widget(NewScenario(NewScenarioMenu, 'newscenariomenu', 'scenarios', name = 'newscenario'))
		self.body.current = 'login'
		
		self.menu.height = '48dp'
		self.menu.size_hint_y = None
		self.use_kivy_settings = False
		self.settings_cls = SettingsWithSidebar
		
		screen =  AnchorLayout(anchor_x='right', anchor_y='top')
		screen.add_widget(self.body)
		screen.add_widget(self.menu)
		
# 		screen = BoxLayout(orientation='vertical')
# 		screen.add_widget(self.menu)
# 		screen.add_widget(self.body)
				
		return screen

	def send_request(self, callback, body):
		headers = {'Content-type': 'application/json'}
		return UrlRequest(url = self.server,
						  on_success = callback,
						  req_body = dumps(body),
						  req_headers = headers)
		
	def build_settings(self, settings, *args, **kwargs):
		settings.register_type('string_long', SettingString)
		settings.register_type('num_int', SettingNumeric)
		
		def custom_on_config_change(config, section, key, value):
			
			self.send_request(None,
							  {'command': 'set',
							  'id': section,
					 	 	  'settings': {key: value}})
			
			print {'command': 'set',
				   'id': section,
				   'settings': {key: value}}
			
		settings.on_config_change = custom_on_config_change
				
		def build_my_settings(settings, req, result):
		
			for settable in result:
				yeah_id = settable[0]
				settings_format = settable[1]
				my_settings = settable[2]
				
				print yeah_id, settings_format, my_settings
				
				config = ConfigParser()
				config.setdefaults(yeah_id, my_settings)
				settings.add_json_panel(my_settings['name'], config, data=dumps(settings_format))
		
		def get_settables(settings, req, result):
		
			self.send_request(partial(build_my_settings, settings),
					  				  {'command': 'get_settings',
					   			 	   'ids': result})
		
		def get_settables_ids(settings):
		
			self.send_request(partial(get_settables, settings),
					  		  {'command': 'get_list_ids',
							   'list': 'settables'})
		
		get_settables_ids(settings)
		
if __name__ == '__main__':
	
	Majordom().run()
	