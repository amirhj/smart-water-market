from functions import Functions
from pareto import get_pareto_frontier_by_point
from util import maxArgs
import random

class Agent:
	def __init__(self, name, fg, ms, opt):
		self.name = name
		self.fg = fg
		self.ms = ms
		self.opt = opt

		self.pareto_frontier = []
		self.neighbours_indecies = {}
		self.functions_indecies = {}
		self.variable = self.fg.variables[self.name]
		self.state = None

		# index 0 is variable itself
		i = 1
		for n in self.variable.neighbours:
			self.neighbours_indecies[n] = i
			i += 1

		i = 0
		for f in self.variable.functions:
			self.functions_indecies[f] = i
			i += 1

	def set_neighbours_values(self, value_indecies):
		state = [value_indecies[self.name]]
		for n in self.variable.neighbours:
			state.append(value_indecies[n])
		self.state = tuple(state)

		raw_set = self.pareto_frontier + [(self.state, self.get_function_values(self.state))]
		self.pareto_frontier = get_pareto_frontier_by_point(raw_set)

	def set_taken_actions(self, actions):
		new_state = list(self.state)
		for n in self.variable.neighbours:
			action = actions[n]
			if action == 'inc':
				new_state[self.neighbours_indecies[n]] += 1
			elif action == 'dec':
				new_state[self.neighbours_indecies[n]] -= 1

		action = actions[self.name]
		if action == 'inc':
			new_state[0] += 1
		elif action == 'dec':
			new_state[0] -= 1

		self.state = tuple(new_state)

		raw_set = self.pareto_frontier + [(self.state, self.get_function_values(self.state))]
		self.pareto_frontier = get_pareto_frontier_by_point(raw_set)


	def get_action(self):
		new_points = self.get_possible_moves()
		action_values = self.evaluate(new_points)
		action = random.choice(maxArgs(action_values))

		if len(action_values.values()) == 0:
			action = 'hold'

		return action

	def get_possible_moves(self):
		variable = [self.name] + [n for n in self.neighbours_indecies]
		index = {n:0 for n in self.neighbours_indecies}
		index[self.name] = 0
		domain = {n:[-1, 0, +1] for n in self.neighbours_indecies}
		domain[self.name] = [-1, 0, +1]
		actions = {-1: 'dec', 0:'hold', 1:'inc'}

		new_points = {'dec': [], 'hold': [], 'inc': []}

		functions = Functions(self.fg)

		while index[variable[0]] < len(domain[variable[0]]):
			new_state = []
			action_profile = []
			variables_values = {}

			all_in_boundaries = True
			for v in variable:
				value = self.state[0]
				if v in self.neighbours_indecies:
					value = self.state[self.neighbours_indecies[v]]

				i = value + domain[v][index[v]]
				if i >= 0 and i < self.fg.variables[v].domain_size:
					new_state.append(i)
					action_profile.append(actions[domain[v][index[v]]])
					variables_values[v] = self.fg.variables[v].domain[i]
				else:
					all_in_boundaries = False
					break

			if all_in_boundaries:
				function_values = []
				for f in self.variable.functions:
					function_values.append(functions.calculate(f, variables_values))

				new_points[action_profile[0]].append(((tuple(action_profile), tuple(new_state)), tuple(function_values)))
			
			for i in reversed(variable):
				if index[i] < len(domain[i]):
					index[i] += 1
					if index[i] == len(domain[i]):
						if i != variable[0]:
							index[i] = 0
					else:
						break

		return new_points

	def evaluate(self, points):
		action_values = {'dec':None, 'hold':None, 'inc':None}

		for a in points:
			for p in points[a]:
				reward = 0
				raw_set = self.pareto_frontier + [(p[0][1], p[1])]
				new_pareto_frontier = get_pareto_frontier_by_point(raw_set)
				if (p[0][1], p[1]) in new_pareto_frontier:
					reward += 1
					reward += self.evaluate_miner_point(self.get_function_values(self.state), p[1])
				else:
					reward = -10

				if reward > action_values[a] or action_values[a] is None:
					action_values[a] = reward

		return action_values

	def get_function_values(self, state):
		#variables_values = {n: self.fg.variables[n].domain[state[self.neighbours_indecies[n]]] for n in self.neighbours_indecies}
		variables_values = {}
		for n in self.neighbours_indecies:
			i = self.neighbours_indecies[n]
			ii = state[i]
			try:
				iii = self.fg.variables[n].domain[ii]
			except:
				print n,i,ii, len(self.fg.variables[n].domain), self.fg.variables[n].domain_size
				raise 'boo'
			variables_values[n] = iii

		variables_values[self.name] = self.fg.variables[self.name].domain[state[0]]

		functions = Functions(self.fg)

		function_values = []
		for f in self.variable.functions:
			function_values.append(functions.calculate(f, variables_values))

		return tuple(function_values)

	def evaluate_miner_point(self, current_point, new_point):
		reward = 0
		for i in range(len(current_point)):
			if new_point[i] < current_point[i]:
				reward += 2
			elif new_point[i] == current_point[i]:
				reward += 0.5
		return reward

