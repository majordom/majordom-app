# -*- coding: utf-8 -*-

from json import dumps

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import (ObjectProperty,
							 ListProperty,
							 StringProperty,
							 NumericProperty,
							 BooleanProperty)
from kivy.uix.switch import Switch
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.screenmanager import Screen
from kivy.network.urlrequest import UrlRequest

class MainWidget(BoxLayout):
	
	manager = ObjectProperty(None)
	server = StringProperty('http://127.0.0.1:8080/')

	def __init__(self):
		super(MainWidget, self).__init__()
		self.server = 'http://127.0.0.1:8080/'
		
class MainScreen(BoxLayout, Screen):
	
	server = StringProperty('http://127.0.0.1:8080/')
	infos = ListProperty([])
	actions = ListProperty([])
	
	def on_pre_enter(self):
		self.refresh()
		Clock.schedule_interval(self.refresh, 2)

	def refresh(self, *args):
		
		def change_actions(request, result):
			self.actions = result
			self.displaybox.refresh()
		
		def get_actions(request, result):
			ids = result
			
			headers = {'Content-type': 'application/json'}
			body = dumps(
						{'command': 'get_actions',
						'ids': ids})
			req = UrlRequest(
							url = self.server,
							on_success = change_actions,
							req_body = body,
							req_headers = headers)
		
		def change_infos(request, result):
			self.infos = result
			
			headers = {'Content-type': 'application/json'}
			body = dumps(
						{'command': 'get_list_ids',
	 					'list': 'actions'})
			req = UrlRequest(
							url = self.server,
							on_success = get_actions,
							req_body = body,
							req_headers = headers)
			
		def get_infos(request, result):
			ids = result
			
			headers = {'Content-type': 'application/json'}
			body = dumps(
						{'command': 'get_infos',
						'ids': ids})
			req = UrlRequest(
							url = self.server,
							on_success = change_infos,
							req_body = body,
							req_headers = headers)
			
		headers = {'Content-type': 'application/json'}
		body = dumps(
					{'command': 'get_list_ids',
 					'list': 'informations'})
		req = UrlRequest(
						url = self.server,
						on_success = get_infos,
						req_body = body,
						req_headers = headers)

class InfoDisplay(BoxLayout):
	info = ObjectProperty()
	yeah_id = StringProperty(0)
	name = StringProperty('')
	description = StringProperty('')
	value = BooleanProperty(0)
	switch = ObjectProperty(Switch)
	
	
	def __init__(self, info):
		super(InfoDisplay, self).__init__()

		self.yeah_id = info['id']
		self.name = info['name']
		self.description = info['description']
		if len(info['values']) > 0: self.value = info['values'][-1][0]
		else: self.value = 0
		
		if self.value:
			self.switch.active = True
		else:
			self.switch.active = False

class ActionDisplay(BoxLayout):
	action = ObjectProperty()
	yeah_id = StringProperty(0)
	name = StringProperty('')
	description = StringProperty('')
	button = ObjectProperty()
	
	def __init__(self, action):
		super(ActionDisplay, self).__init__()

		self.yeah_id = action['id']
		self.name = action['name']
		self.description = action['description']
		
	def execute_action(self):

		headers = {'Content-type': 'application/json'}
		body = dumps({'command': 'execute_action',
					  'id': self.yeah_id,
					  'args': {}})
		req = UrlRequest(
						url = self.app.server,
						req_body = body,
						req_headers = headers)
		print "req sent"
		
	

class DisplayBox(StackLayout):
	
	infos = ListProperty([])
	actions = ListProperty([])
	
	def refresh(self):
		self.clear_widgets()
		for info in self.infos:
			self.add_widget(InfoDisplay(info))
		for action in self.actions:
			self.add_widget(ActionDisplay(action))

class MyApp(App):
	
	server = StringProperty('http://127.0.0.1:8080/')
	
	def send_request(self, request, callback):
		headers = {'Content-type': 'application/json'}
		# TODO: il faudra ajouter tout ce qui est relatif à la session ici 
		body = dumps(request)
		req = UrlRequest(
						url = self.server,
						req_body = body,
						req_headers = headers)
		print "req sent"
		
	def build(self):
		
		self.main_widget = MainWidget()
		return self.main_widget 

if __name__ == '__main__':
	
	MyApp().run()
	