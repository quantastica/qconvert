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

from .qconvert_base import gate_defs, eval_mathjs_string
from .qconvert_qobj import QConvertQobj

class QobjToPyquil(QConvertQobj):

	def on_start(self, data):

		info = data["info"]

		options = self.options

		self.result = ""

		#
		# Used for imports
		#
		self.imports = ""

		#
		# Used for declarations
		#
		self.program_head = ""

		#
		# Used for program body
		#
		self.program_body = ""

		#
		# Used for user defined gates
		#
		self.def_gate_names = []
		self.def_param_names = []
		self.def_params = ""
		self.def_gates = ""
		self.decl_gates = ""
		self.assign_gates = ""
		self.append_gates = ""

		#
		# Create imports
		#
		self.imports += "from pyquil import Program, get_qc\n"
		self.imports += "from pyquil.gates import *\n"
		if info["return_state_vector"]:
			self.imports += "from pyquil.api import WavefunctionSimulator\n"

		#
		# Create Program instance. Add rewiring if user wants exec code for simulated QPU/QPU
		#
		if "lattice" in options and options["lattice"] is not None and options["lattice"] != "statevector_simulator" and options["lattice"] != "qasm_simulator" and (options["lattice"].find("q-qvm") < 0):
			self.program_head += "p = Program('PRAGMA INITIAL_REWIRING \"PARTIAL\"')\n"
		else:
			self.program_head += "p = Program()\n"

		#
		# Declare classical registers
		#
		if "memory_slots" in info:
			memory_slots = info["memory_slots"]
			if memory_slots > 0:
				self.program_head += "\n"
				if not info["classical_control_present"]:
					self.program_head += "ro = p.declare('ro', memory_type='BIT', memory_size=" + str(memory_slots) + ")\n"
				else:
					if memory_slots > 1:
						self.program_head += "sha_reg = p.declare('sha_reg', memory_type='INTEGER', memory_size=" + str(memory_slots) + ")\n"
						self.program_head += "int_reg = p.declare('int_reg', memory_type='INTEGER', memory_size=" + str(memory_slots) + ")\n"
						self.program_head += "ro = p.declare('ro', memory_type='BIT', memory_size=" + str(memory_slots) + ", shared_region='sha_reg')\n"
					else:
						self.program_head += "ro = p.declare('ro', memory_type='BIT', memory_size=" + str(memory_slots) + ")\n"

					self.program_head += "bit_reg = p.declare('bit_reg', memory_type='BIT', memory_size=1)\n"



	def on_measure(self, data):
		self.program_body += "p += MEASURE(" + str(data["qubit"]) + ", ro[" + str(data["memory"]) + "])\n"


	def on_gate(self, data):

		info = data["info"]
		options = self.options

		#
		# Do we support this gate?
		#
		if "gate_def" not in data or data["gate_def"] is None:
			raise Exception("Definition not found for gate \"" + data["name"] + "\".")

		gate_def = data["gate_def"]

		#
		# Find pyQuil exportInfo
		#
		while True:
			if "exportInfo" not in gate_def:
				raise Exception("No export info for gate \"" + data["name"] + "\".")

			if "pyquil" not in gate_def["exportInfo"]:
				#
				# Quil exportInfo is enough
				#
				if "quil" not in gate_def["exportInfo"]:
					raise Exception("No pyQuil export info for gate \"" + data["name"] + "\".")
				else:
					pyquil_info = gate_def["exportInfo"]["quil"]
			else:
				pyquil_info = gate_def["exportInfo"]["pyquil"]

			if "replacement" in pyquil_info:
				replacement_name = pyquil_info["replacement"]["name"]
				if replacement_name not in gate_defs:
					raise Exception("Definition not found for gate \"" + data["name"] + "\"'s replacement \"" + replacement_name + "\".")

				gate_def = gate_defs[replacement_name]

				data["name"] = replacement_name
				data["gate_def"] = gate_def
				data["params"] = []

				if "params" in pyquil_info["replacement"]:
					rep_params_dict = pyquil_info["replacement"]["params"]
					rep_params = []
					for rep_param_name in rep_params_dict:
						rep_param_eval = eval_mathjs_string(rep_params_dict[rep_param_name], params=None)
						rep_params.append(rep_param_eval)
					data["params"] = rep_params
			else:
				break;



		#
		# User defined gate?
		#
		user_defined_gate = False
		if "array" in pyquil_info and pyquil_info["array"] is not None and len(pyquil_info["array"]) > 0:
			#
			# User defined gate
			#
			user_defined_gate = True

			#
			# Already defined?
			#
			if data["name"] not in self.def_gate_names:
				#
				# def gate
				#
				if len(self.def_gate_names) == 0:
					#
					# Imports required for def gate
					#
					self.imports += "from pyquil.quilatom import Parameter, quil_sin, quil_cos, quil_sqrt, quil_exp, quil_cis\n"
					self.imports += "from pyquil.quilbase import DefGate\n"
					self.imports += "import numpy as np\n"

				self.def_gate_names.append(data["name"])

				param_list = ""
				if "params" in pyquil_info and pyquil_info["params"] is not None and len(pyquil_info["params"]) > 0:
					for param_name in pyquil_info["params"]:
						if param_name not in self.def_param_names:
							self.def_param_names.append(param_name) 
							self.def_params += "p_" + param_name + " = Parameter('" + param_name + "')\n"
						if param_list != "":
							param_list += ", "
						param_list += "p_" + param_name

				self.def_gates += data["name"] + "_matrix = np.array(" + pyquil_info["array"] + ")\n"

				self.decl_gates += data["name"] + "_defgate = DefGate('" + data["name"] + "', " + data["name"] + "_matrix, [" + param_list + "])\n"

				self.assign_gates += data["name"]  + " = " + data["name"] + "_defgate.get_constructor()\n"

				self.append_gates += "p += " + data["name"] + "_defgate\n"

		got_condition = False
		if data["condition"] is not None:
			got_condition = True

			condition = data["condition"]

			if info["memory_slots"] == 1:
				self.program_body += "\n"
				self.program_body += "p += MOVE(bit_reg, ro[" + str(condition["memory"]) + "])\n"
				if condition["val"] == 0:
					self.program_body += "p += NOT(bit_reg)\n"
				self.program_body += "p.if_then(bit_reg, Program("
			else:
				self.program_body += "\n"
				self.program_body += "p += MOVE(int_reg, sha_reg)\n"
				self.program_body += "p += AND(int_reg, " + hex(condition["mask"]) + ")\n"
				self.program_body += "p += EQ(bit_reg, int_reg, " + hex(condition["val"]) + ")\n"
				self.program_body += "p.if_then(bit_reg, Program("
		else:
			self.program_body += "p += "

		#
		# Gate name
		#
		self.program_body += pyquil_info["name"]
		self.program_body += "("

		#
		# Gate params
		#
		param_count = 0
		if "params" in pyquil_info and len(pyquil_info["params"]) > 0:
			for param_name in gate_def["params"]:
				if param_name not in pyquil_info["params"]:
					raise Exception("Param \"" + param_name + "\" not found in pyQuil export info for gate \"" + data["name"] + "\".")

				param_index = pyquil_info["params"].index(param_name)
				if param_index >= len(data["params"]):
					raise Exception("Param \"" + param_name + "\" not specified in Qobj for gate \"" + name + "\".")

				if param_count > 0:
					self.program_body += ", "
				param_count += 1

				self.program_body += str(data["params"][param_index])

		if param_count > 0:
			if user_defined_gate:
				self.program_body += ")("
			else:
				self.program_body += ", "
		#
		# Target qubits
		#
		qubit_count = 0
		for qubit in data["qubits"]:
			if qubit_count > 0:
				self.program_body += ", "
			qubit_count += 1
			self.program_body += str(qubit)

		self.program_body += ")"

		if got_condition:
			self.program_body += "))\n"

		self.program_body += "\n"


	def on_end(self, data):
		info = data["info"]
		options = self.options

		#
		# Executable code
		#
		if "lattice" in options and options["lattice"] is not None and options["lattice"] != "qasm_simulator" and (options["lattice"].find("q-qvm") < 0):
			lattice_name = options["lattice"]

			#
			# Lattice name is given
			#
			if info["return_state_vector"] or lattice_name == "statevector_simulator":
				#
				# QVM: Statevector
				#
				self.program_body += "qc = WavefunctionSimulator()\n"
				if info["create_exec_code"]:
					self.program_body += "\n"
					self.program_body += "wf = qc.wavefunction(p)\n"
					self.program_body += "print(wf)\n"
			else:
				#
				# QPU
				#

				#
				# Multishot?
				#
				if "shots" in options and options["shots"] is not None and options["shots"] > 1:
					self.program_body += "p.wrap_in_numshots_loop(" + str(options["shots"]) + ")\n"
					self.program_body += "\n"

				#
				# get_qc
				#
				if "as_qvm" in options and options["as_qvm"]:
					self.program_body += "qc = get_qc('" + lattice_name + "', as_qvm=True)\n"
				else:
					self.program_body += "qc = get_qc('" + lattice_name + "')\n"

				#
				# set seed if needed
				#
				if "seed" in options and options["seed"]:
					self.program_body += "qc.qam.random_seed = %d\n" % int(options['seed'])

				#
				# Compile
				#
				self.program_body += "\n"
				self.program_body += "ex = qc.compile(p)\n"

				#
				# Run
				#
				if info["create_exec_code"]:
					self.program_body += "print(qc.run(ex))\n"
		else:
			#
			# QVM: If lattice is not given or lattice name is "qasm_simulator"
			#

			#
			# Multishot?
			#
			if "shots" in options and options["shots"] is not None and options["shots"] > 1:
				self.program_body += "p.wrap_in_numshots_loop(" + str(options["shots"]) + ")\n"
				self.program_body += "\n"

			#
			# get_qc
			#
			lattice_name = str(info["qubits"]) + "q-qvm"
			self.program_body += "qc = get_qc('" + lattice_name + "')\n"

			#
			# set seed if needed
			#
			if "seed" in options and options["seed"]:
				self.program_body += "qc.qam.random_seed = %d\n" % int(options['seed'])

			#
			# Run
			#
			if info["create_exec_code"]:
				self.program_body += "\n"
				self.program_body += "print(qc.run(p))\n"
			else:
				self.program_body += "ex = p\n"
		#
		# Assemble the code
		#
		code = ""
		code += self.imports
		code += "\n"

		if len(self.def_gate_names) > 0:
			code += self.def_params
			code += "\n"
			code += self.def_gates
			code += "\n"
			code += self.decl_gates
			code += "\n"
			code += self.assign_gates
			code += "\n"
			code += "\n"

		code += self.program_head
		code += "\n"

		if len(self.def_gate_names) > 0:
			code += self.append_gates
			code += "\n"
			code += "\n"

		code += self.program_body

		self.result = code


def qobj_to_pyquil(qobj, options):
	converter = QobjToPyquil()

	pyquil = converter.convert(qobj, options)

	return pyquil
