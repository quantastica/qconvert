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
import re

gate_defs_path = os.path.join(os.path.dirname(__file__), "gate_defs.json")
with open(gate_defs_path, encoding="utf-8") as file:
	gate_defs = json.load(file, encoding="utf-8")

from cmath import *

def is_float_str(s):
	try:
		float(s)
		return True
	except:
		return False

import functools

@functools.lru_cache(maxsize=1024)
def compile_expression(s):
	expression = ""
	tokens = re.findall(r"(\b\w*[\.]?\w+\b|[\(\)\+\*\-\/])", s)
	prev_tok = None
	for tok in tokens:
		# replace iota char 'i' with 'j'
		if tok == "i" or tok == "j":
			if prev_tok is None or is_float_str(prev_tok) == False:
				tok = "1j"
			else:
				tok = "j"

		# lambda appears as variable name in some expressions, but is reserved word in python
		if tok == "lambda":
			tok = "_lambda"

		expression += tok
		prev_tok = tok
	return compile(expression,"",'eval')

def eval_mathjs_string(s, params):
	# evaluate expression
	prepared = compile_expression(s)

	# cleanup params
	clean_params = {}
	if params is not None:
		for param_name in params:
			# lambda appears as variable name in some expressions, but is reserved word in python
			if param_name == "lambda":
				clean_name = "_lambda"
			else:
				clean_name = param_name

			clean_params[clean_name] = params[param_name]

	return eval(prepared, None, clean_params)

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

		if len(self.results)>0 and not all_experiments:
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
