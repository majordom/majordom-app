# -*- coding: utf-8 -*-

from kivy.properties import ObjectProperty

from custom_classes import ScreenWithMenu, Menu

class LoginMenu(Menu):
	pass

class Login(ScreenWithMenu):
	
	server = ObjectProperty()
	username = ObjectProperty()
	password = ObjectProperty()
	
	def connect(self):
		self.app.server = self.server.text
		# TODO: procédure de connexion avec user et mot de passe
		self.app.body.current = 'home'