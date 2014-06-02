# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.clock import Clock
from kivy.config import ConfigParser
from kivy.graphics import Line, Color
from kivy.properties import ObjectProperty, StringProperty, ListProperty, BooleanProperty
from kivy.uix.button import Button
from kivy.uix.scatter import Scatter
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.bubble import Bubble, BubbleButton
from kivy.uix.settings import Settings, SettingsWithNoMenu, SettingString, SettingNumeric

from json import dumps
from custom_classes import ScreenWithMenu, Menu

class Scenarios(ScreenWithMenu):
	scenarios_list = ObjectProperty()
	
	def on_pre_enter(self):
		super(Scenarios, self).on_pre_enter()
		
		def display(req, result):
			
			self.scenarios_list.clear_widgets()
			for scenario in result:
				scenario_id = scenario[0]
				scenario_settings = scenario[2]
				self.scenarios_list.add_widget(Button(text = scenario_settings['name'],
													  id = scenario_id,
													  on_release = self.edit_scenario,
													  size_hint = (1, None),
													  height = '30dp',
													  pos_hint= {'top': 1}))
		
		def get_scenarios(req, result):
			
			self.app.send_request(display,
								  {'command': 'get_settings',
								   'ids': result})
		
		self.app.send_request(get_scenarios,
							  {'command': 'get_list_ids',
							   'list': 'scenarios'})
		
	def edit_scenario(self, button):
		edit_screen = EditScenario(button.id, EditScenarioMenu, 'editscenariomenu', 'scenarios', name = 'editscenario')
		self.app.body.add_widget(edit_screen)
		self.app.body.current = edit_screen.name
	
class ScenariosMenu(Menu):
	pass
		
class NewScenario(ScreenWithMenu):
	
	scenario_name = ObjectProperty()
	description = ObjectProperty()
	
	def on_pre_enter(self):
		super(NewScenario, self).on_pre_enter()
		self.scenario_name.text = ''
		self.description.text= ''
	
	def add_new_scenario(self):
		
		def switch_to_manage(req, result):
			_name = 'edit_scenario_' + str(result)
			edit_screen = EditScenario(result, EditScenarioMenu, 'editscenariomenu', 'scenarios', name = 'editscenario')
			self.app.body.add_widget(edit_screen)
			self.app.body.current = edit_screen.name

		self.app.send_request(switch_to_manage,
							  {'command': 'add_scenario',
							   'settings': {'name': self.scenario_name.text,
								  			'description': self.description.text}})

class NewScenarioMenu(Menu):
	pass
		
class EditScenario(ScreenWithMenu):
	
	title = StringProperty('')
	scenario = ObjectProperty()
	scenario_canvas = ObjectProperty()
	blocks = ListProperty()
	links = ListProperty()
	active = BooleanProperty()
	
	def __init__(self, scenario_id, *args, **kwargs):
		super(EditScenario, self).__init__(*args, **kwargs)
		self.scenario_id = scenario_id
		self.scenario = None
		self.state = 'waiting_first'
		self.first_node = None
		self.active = False
		
	def on_pre_enter(self):
		super(EditScenario, self).on_pre_enter()
		
		def display_scenario(req, result):
			self.scenario = result
			print self.scenario
			#self.title = 'Editing scenario ' + self.scenario['settings']['name']
			self.active = self.scenario['active']
			
			for json_block in self.scenario['blocks']:
				self.add_block(json_block)
			
			for json_link in self.scenario['links']:
				self.add_link(json_link)
				
			self.redraw()
		
		Clock.schedule_interval(self.update_block_positions, 2)
										
		self.app.send_request(display_scenario,
							  {'command': 'get_scenario',
							   'id': self.scenario_id})
	
	def on_leave(self):
		Clock.unschedule(self.update_block_positions)
		self.app.body.remove_widget(self)
	
	def update_block_positions(self, *args):
		
		self.app.send_request(None,
							  {'command': 'update_block_positions',
							   'scenario_id': self.scenario_id,
							   'block_positions': [{'block_id': block.yeah_id, 'position': block.pos} for block in self.blocks]})
	
	def redraw(self):
		for link in self.links: 
			self.scenario_canvas.remove_widget(link)
			self.scenario_canvas.add_widget(link)
			link.refresh()
		
		for block in self.blocks:
			self.scenario_canvas.remove_widget(block)
			self.scenario_canvas.add_widget(block)

	def get_node(self, yeah_id):
		result = False
		for block in self.blocks:
			for node in block.input_nodes + block.output_nodes:
				if node.yeah_id == yeah_id:
					result = node
		return result
	
	def node_touched(self, node, touch):
		
		print node
		
		def reset():
			self.state = 'waiting_first'
			self.first_node = None
			for block in self.blocks:
				for node in block.output_nodes + block.input_nodes:
					node.activate() 
		
		def display_new_link(req, result):
			
			self.add_link(result)
			reset()

		if node.collide_point(*touch.pos):
			if self.state == 'waiting_first':
				self.first_node = node
				self.state = 'waiting_second'
				for block in self.blocks:
					for other_node in block.output_nodes + block.input_nodes:
						if not other_node.is_compatible_with(node):
							other_node.deactivate()
						if other_node.multiplicity == 'simple' and other_node in [l.dst_node for l in self.links]:
							other_node.deactivate()
			elif self.state == 'waiting_second':
				print 'waiting second'
				if node == self.first_node:
					reset()
				elif node.is_compatible_with(self.first_node):
					print 'node compatible!'
					if not(node.multiplicity == 'simple' and node in [l.dst_node for l in self.links]):	
						print 'connecting...'
						if OutputNode in self.first_node.__class__.__mro__:
							src = self.first_node
							dst = node
						else:
							src = node
							dst = self.first_node
									
						self.app.send_request(display_new_link,
											  {'command': 'add_link',
											   'scenario_id': self.scenario_id,
											   'src_id': src.yeah_id,
											   'dst_id': dst.yeah_id})
			
	def add_block(self, json_block):
		print json_block
		new_block = Block(self, json_block['id'], json_block['name'], json_block['settings'], json_block['settings_format'], json_block['input_nodes'], json_block['output_nodes'], json_block['position'])
		self.blocks.append(new_block)
		self.scenario_canvas.add_widget(new_block)
		return new_block 
	
	def add_link(self, json_link):
		print 'add link'
		new_link = Link(self, json_link['id'], self.get_node(json_link['src_node']), self.get_node(json_link['dst_node'])) 
		self.links.append(new_link)
		self.scenario_canvas.add_widget(new_link)
		self.redraw()
	
	def remove_block(self, block):
		
		self.blocks.remove(block)
		self.scenario_canvas.remove_widget(block)
		
		for link in list(self.links):
			if (link.src_node in block.input_nodes + block.output_nodes) or (link.dst_node in block.input_nodes + block.output_nodes):
				self.links.remove(link)
				self.scenario_canvas.remove_widget(link)
		
		self.app.send_request(None,
							  {'command': 'remove_block',
							   'scenario_id': self.scenario_id,
							   'block_id': block.yeah_id})
		
		print 'block removed'
	
	def remove_link(self, link):
		
		self.links.remove(link)
		self.scenario_canvas.remove_widget(link)
		
		self.app.send_request(None,
							  {'command': 'remove_link',
							   'scenario_id': self.scenario_id,
							   'link_id': link.yeah_id})
		
		print 'link removed'
	
	def open_add_popup(self, purpose):
		AddPopup(self, purpose).open()

	def toggle_scenario(self):
		
		def do_toggle(req, result):
			self.active = result['active']
			self.menu.toggle_button.text = 'Deactivate' if self.active else 'Activate'
		
		self.app.send_request(do_toggle,
							  {'command': 'toggle_scenario',
							   'id': self.scenario_id,
							   'active': not self.active})
	
	def display_block_settings(self, block):
		BlockSettingsPopup(self, block).open()
				
class EditScenarioMenu(Menu):
	
	toggle_button = ObjectProperty()
	
	def on_pre_enter(self, *args, **kwargs):
		super(EditScenarioMenu, self).on_pre_enter(*args, **kwargs)
		self.toggle_button.text = 'Deactivate' if self.body.active else 'Activate'
	
	def on_leave(self):
		self.body.app.menu.remove_widget(self)
		
	def toggle_button_pressed(self):
		self.body.toggle_scenario()
		
class BlockSettingsPopup(Popup):
	
	def __init__(self, scenario_screen, block, *args, **kwargs):
		super(BlockSettingsPopup, self).__init__(*args, **kwargs)
		
		self.app = App.get_running_app()
		self.title = 'Block settings'
		self.block = block
		self.scenario_screen = scenario_screen
		
		self.settings = SettingsWithNoMenu()
		self.settings.on_config_change = self.on_config_change
		self.settings.register_type('string_long', SettingString)
		self.settings.register_type('num_int', SettingNumeric)
		self.settings.register_type('num', SettingNumeric)
		
		config = ConfigParser()
		config.setdefaults(block.yeah_id, block.settings)
		self.settings.add_json_panel(block.settings['name'], config, data=dumps(block.settings_format))		
		self.content = self.settings
	
	def on_config_change(self, config, section, key, value):
		
		self.block.settings[key] = value
		self.app.send_request(None,
							  {'command': 'set_block',
							   'scenario_id': self.scenario_screen.scenario_id,
							   'block_id': self.block.yeah_id,
							   'settings': {key: value}})

class AddPopup(Popup):
	
	purpose = StringProperty('')
	
	def __init__(self, scenario_screen, purpose, *args, **kwargs):
		super(AddPopup, self).__init__(*args, **kwargs)
		
		self.app = App.get_running_app()
		self.scenario_screen = scenario_screen
		self.purpose = purpose
		
		if self.purpose == 'block':
			self.title = 'Add a block'
			self.get_command = 'get_block_models'
			self.add_command = 'add_block'
		elif self.purpose == 'action':
			self.title = 'Add an action'
			self.get_command = 'get_actions'
			self.add_command = 'add_action'
		elif self.purpose == 'info':
			self.title = 'Add an info'
			self.get_command = 'get_infos'
			self.add_command = 'add_info'
		
		self.scenario_screen.app.send_request(self.display_list,
							  				  {'command': self.get_command})
	
	def display_list(self, req, result):
		self.list.clear_widgets()
		
		for element in result:
			self.list.add_widget(Button(text = element['name'],
										id = element['id'],
										on_release = self.choice_made,
										size_hint = (1, None),
										height = '30dp',
										pos_hint= {'top': 1}))
	
	def choice_made(self, button):

		self.app.send_request(self.add_element,
							  {'command': self.add_command,
							   'scenario_id': self.scenario_screen.scenario_id,
							   'id': button.id,
							   'settings': None})

	def add_element(self, req, result):
		new_block = self.scenario_screen.add_block(result)
		new_block.pos = (-self.scenario_screen.scenario_canvas.pos[0], -self.scenario_screen.scenario_canvas.pos[1])
		self.dismiss()

class Block(Scatter):
	
	yeah_id = StringProperty()
	input_nodes = ListProperty()
	output_nodes = ListProperty()
	name = StringProperty()
	block_layout = ObjectProperty()
	scenario_screen = ObjectProperty()
	
	def __init__(self, scenario_screen, yeah_id, name, settings, settings_format, input_nodes, output_nodes, position, *args, **kwargs):
		super(Block, self).__init__(*args, **kwargs)
		
		self.scenario_screen = scenario_screen
		self.yeah_id = yeah_id
		self.name = name
		self.settings = settings
		self.settings_format = settings_format
		self.pos = position
		self.bubble = None
		
		for i, input_node in enumerate(input_nodes):
			new_input_node = InputNode(self, input_node['id'], input_node['type'], input_node['name'], pos_hint = {'center_x': 0, 'center_y': float(i+1)/(len(input_nodes)+1)}, multiplicity = input_node['multiplicity'])
			new_input_node.bind(on_touch_down = self.scenario_screen.node_touched) 
			self.input_nodes.append(new_input_node)
			self.block_layout.add_widget(new_input_node)
			
		for i, output_node in enumerate(output_nodes):
			new_output_node = OutputNode(self, output_node['id'], output_node['type'], output_node['name'], pos_hint = {'center_x': 1, 'center_y': float(i+1)/(len(output_nodes)+1)})
			new_output_node.bind(on_touch_down = self.scenario_screen.node_touched) 
			self.output_nodes.append(new_output_node)
			self.block_layout.add_widget(new_output_node)
			
# 	def on_pos(self, *args, **kwargs):
# 		
# 		if self.scenario_screen != None:
# 			App.get_running_app().send_request(None,
# 											   {'command': 'set_block_position',
# 											    'scenario_id': self.scenario_screen.scenario_id,
# 												'block_id': self.yeah_id,
# 												'position': self.pos})
	
	def on_touch_down(self, touch):
		touch.push()
		ret = super(Block, self).on_touch_down(touch)
		if self.bubble != None:
			self.block_layout.remove_widget(self.bubble)
			self.bubble = None
		touch.pop()
		return ret
	
	def on_touch_up(self, touch):
		touch.push()
		ret = super(Block, self).on_touch_up(touch)
		if self.collide_point(*touch.pos):
			if touch.is_double_tap:
				if self.bubble == None:
					self.bubble = BlockBubble(self)
					if len(self.settings_format) > 1:
						self.bubble.add_widget(BubbleButton(text = 'Settings', on_press = self.display_settings))
					self.block_layout.add_widget(self.bubble)
		touch.pop()
		return ret
	
	def remove(self):
		self.scenario_screen.remove_block(self)
	
	def display_settings(self, *args, **kwargs):
		self.scenario_screen.display_block_settings(self)

class BlockBubble(Bubble):
	
	block = ObjectProperty()
	
	def __init__(self, block, *args, **kwargs):
		super(BlockBubble, self).__init__(*args, **kwargs)
		
		self.block = block
	
	def remove_block(self, *args, **kwargs):
		self.block.remove()
		
class Node(FloatLayout):
	
	yeah_id = StringProperty()
	type = StringProperty()
	name = StringProperty()
	
	def __init__(self, block, yeah_id, value_type, name, multiplicity = 'simple', *args, **kwargs):
		super(Node, self).__init__(*args, **kwargs)
		
		self.block = block
		self.yeah_id = yeah_id
		self.type = value_type
		self.name = name
		self.multiplicity = multiplicity
	
	def activate(self):
		self.disabled = False
	
	def deactivate(self):
		self.disabled = True
	
	
class InputNode(Node):
	
	def is_compatible_with(self, node):
				
		check = [self.type == node.type,
				 self.block != node.block,
				 OutputNode in node.__class__.__mro__]
		
		return (False not in check)

class OutputNode(Node):
	
	def is_compatible_with(self, node):
		check = [self.type == node.type,
				 self.block != node.block,
				 InputNode in node.__class__.__mro__]
		
		return (False not in check)

class Link(FloatLayout):
	
	line = ObjectProperty()
	
	def __init__(self, scenario_screen, yeah_id, src_node, dst_node, *args, **kwargs):
		super(Link, self).__init__(*args, **kwargs)
		
		self.scenario_screen = scenario_screen
		self.bubble = None
		
		print src_node, dst_node
		
		self.yeah_id = yeah_id
		self.src_node = src_node
		self.dst_node = dst_node
		
		src_node.block.bind(pos=self.refresh)
		dst_node.block.bind(pos=self.refresh)
		src_node.bind(pos=self.refresh)
		dst_node.bind(pos=self.refresh)
		
	def refresh(self, *args, **kwargs):
		
		pos = []
		pos.append(self.src_node.block.x + self.src_node.center_x)
		pos.append(self.src_node.block.y + self.src_node.center_y)
		pos.append(self.dst_node.block.x + self.dst_node.center_x)
		pos.append(self.dst_node.block.y + self.dst_node.center_y)
		with self.canvas:
			self.canvas.clear()
			self.canvas.add(Color(80.0/255,80.0/255,80.0/255, 1))
			self.canvas.add(Line(points=pos, width=5))

		self.center_x = (pos[0]+pos[2])/2
		self.center_y = (pos[1]+pos[3])/2
		self.size_hint = (None, None)
		self.size = (50, 50)

	def on_touch_down(self, touch):
		touch.push()
		ret = super(Link, self).on_touch_down(touch)
		if self.bubble != None:
			self.remove_widget(self.bubble)
			self.bubble = None
		touch.pop()
		return ret
	
	def on_touch_up(self, touch):
		touch.push()
		ret = super(Link, self).on_touch_up(touch)
		if self.collide_point(*touch.pos):
			if touch.is_double_tap:
				print 'coucou'
				if self.bubble == None:
					self.bubble = LinkBubble(self)
					self.add_widget(self.bubble)
		touch.pop()
		return ret
	
	def remove(self):
		self.scenario_screen.remove_link(self)

class LinkBubble(Bubble):
	
	link = ObjectProperty()
	
	def __init__(self, link, *args, **kwargs):
		super(LinkBubble, self).__init__(*args, **kwargs)
		
		self.link = link
	
	def remove_link(self, *args, **kwargs):
		self.link.remove()

# class AddBlockPopup(Popup):
# 	
# 	def __init__(self, scenario_screen):
# 		super(AddBlockPopup, self).__init__()
# 		
# 		self.scenario_screen = scenario_screen
# 				
# 		def display_list(req, result):
# 			self.blocks_list.clear_widgets()
# 			
# 			print 'result', result
# 			
# 			for block_model in result:
# 				self.blocks_list.add_widget(Button(text = block_model['name'],
# 												   id = block_model['id'],
# 												   on_release = self.block_chosen,
# 												   size_hint = (1, None),
# 												   height = '30dp',
# 												   pos_hint= {'top': 1}))
# 		
# 		self.scenario_screen.app.send_request(display_list,
# 							  				  {'command': 'get_block_models'})
# 	
# 	def block_chosen(self, button):
# 		
# 		def add_block(req, result):
# 			print 'adding block...'
# 			new_block = self.scenario_screen.add_block(result)
# 			new_block.pos = (-self.scenario_screen.scenario_canvas.pos[0], -self.scenario_screen.scenario_canvas.pos[1])
# 			self.dismiss()
# 				
# 		self.scenario_screen.app.send_request(add_block,
# 							  {'command': 'add_block',
# 							   'scenario_id': self.scenario_screen.scenario_id,
# 							   'block_model_id': button.id,
# 							   'settings': None})

# 	def cancel_link(self):
# 		self.menu.remove_button('cancel_button')
# 		self.state = 'waiting_first'
# 		self.first_node = None
# 		for block in self.blocks:
# 			for node in block.output_nodes + block.input_nodes:
# 				node.activate() 