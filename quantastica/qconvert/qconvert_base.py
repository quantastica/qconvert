# This code is part of quantastica.qconvert
#
# (C) Copyright Quantastica 2019. 
# https://quantastica.com/
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import os
import json

gate_defs_path = os.path.join(os.path.dirname(__file__), "gate_defs.json")
with open(gate_defs_path) as file:
	gate_defs = json.load(file)


from cmath import *
import tokenize
import io

def tokenize_string(s):
	return tokenize.tokenize(io.BytesIO(s.encode('utf-8')).readline)

def eval_mathjs_string(s, params):
	string = s

	result = []
	prev = None
	for tok in tokenize_string(s):
		if tok.type == tokenize.ENCODING:
			encoding = tok.string

		# replace iota char 'i' with 'j'
		if tok.string == "i" or tok.string == "j":
			# single 'i' or 'j' translates to '1j'
			if prev != tokenize.NUMBER:
				result.append((tokenize.NAME, "1j"))
			else:
				result.append((tokenize.NAME, "j"))

		# lambda appears as variable name in some expressions, but is reserved word in python
		elif tok.string == "lambda":
			result.append((tokenize.NAME, "_lambda"))
		else:
			result.append(tok)

		prev = tok.type

	string = tokenize.untokenize(result).decode(encoding)

	clean_params = {}
	if params is not None:
		for param_name in params:
			# lambda appears as variable name in some expressions, but is reserved word in python
			if param_name == "lambda":
				clean_name = "_lambda"
			else:
				clean_name = param_name

			clean_params[clean_name] = params[param_name]

	return eval(string, None, clean_params)


def eval_mathjs_matrix(matrix, params):
	res_matrix = []
	for row in matrix:
		res_row = []
		for cell in row:
			if isinstance(cell, str):
				ev = eval_mathjs_string(cell, params)

				if isinstance(ev, complex):
					res_row.append({ "type": "complex", "re": ev.real, "im": ev.imag })
				else:
					res_row.append(ev)
			else:
				res_row.append(cell)

		res_matrix.append(res_row)

	return res_matrix


class QConvertBase:

	def __init__(self):
		self.clear()

	def clear(self):
		self.result = None
		self.results = []

	def convert(self, input_data, options={ "all_experiments": False }):
		self.clear()

		self.options = options if options is not None else {}

		self.converter(input_data, options)

		all_experiments = False
		if self.options is not None and "all_experiments" in self.options and self.options["all_experiments"]:
			all_experiments = True

		if not all_experiments:
			return self.results[0]

		return self.results

	def on_start(self, data):
		pass

	def on_barrier(self, data):
		pass

	def on_measure(self, data):
		pass

	def on_gate(self, data):
		pass

	def on_end(self, data):
		pass
