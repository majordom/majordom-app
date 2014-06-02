# -*- coding: utf-8 -*-

from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.uix.actionbar import ActionBar 
from kivy.uix.screenmanager import (ScreenManager,
									Screen,
									SlideTransition,
									WipeTransition)

class Menu(Screen):
	
	body = ObjectProperty()
	
	def __init__(self, body, *args, **kwargs):
		super(Menu, self).__init__(*args, **kwargs)
		self.body = body
	
class ScreenWithMenu(Screen):

	menu = ObjectProperty()
	app = ObjectProperty()
	
	def __init__(self, menu_class, menu_name, previous_screen_name, *args, **kwargs):
		super(ScreenWithMenu, self).__init__(*args, **kwargs)
		self.app = App.get_running_app()
		self.menu = menu_class(self, name=menu_name)
		self.app.menu.add_widget(self.menu)
		self.previous = previous_screen_name
		
	def on_pre_enter(self):
		self.app.menu.current = self.menu.name
	
	def go_back(self):
		self.app.body.transition = SlideTransition(direction='right')
		self.app.body.current = self.previous
		self.app.body.transition = SlideTransition()