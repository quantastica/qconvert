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

#
# Load gate definitions on init
#
gate_defs_path = os.path.join(os.path.dirname(__file__), "gate_defs.json")
with open(gate_defs_path) as file:
	gate_defs = json.load(file)


def experiment_to_pyquil(experiment, options = {}):
	if "instructions" not in experiment or len(experiment["instructions"]) == 0:
		return ""

	pyquil = ""

	state_vector = False
	if "lattice" in options and options["lattice"] == "statevector_simulator":
		state_vector = True

	#
	# Imports
	#
	imports = ""
	imports += "from pyquil import Program, get_qc\n"
	imports += "from pyquil.gates import *\n"
	if state_vector:
		imports += "from pyquil.api import WavefunctionSimulator\n"

	#
	# Used for user defined gates
	#
	def_gate_names = []
	def_param_names = []
	def_params = ""
	def_gates = ""
	decl_gates = ""
	assign_gates = ""
	append_gates = ""

	#
	# Does user want to generate qc.run(...) ?
	#
	create_exec_code = False
	if "create_exec_code" not in options or options["create_exec_code"]:
		create_exec_code = True

	#
	# Create Program instance. Add rewiring if user wants exec code for simulated QPU/QPU
	#
	program_head = ""
	if "lattice" in options and options["lattice"] is not None and options["lattice"] != "statevector_simulator" and options["lattice"] != "qasm_simulator" and (options["lattice"].find("q-qvm") < 0):
		program_head += "p = Program('PRAGMA INITIAL_REWIRING \"PARTIAL\"')\n"
	else:
		program_head += "p = Program()\n"

	n_qubits = 0
	memory_slots = 0

	#
	# Do we have header in Qobj?
	#
	if "header" not in experiment:
		raise Exception("Qobj header not found.")

	header = experiment["header"]

	instructions = experiment["instructions"]

	classical_control_present = False
	for instruction in instructions:
		if instruction["name"] == "bfunc":
			classical_control_present = True
			break

	#
	# Declare classical registers
	#
	if "memory_slots" in header:
		memory_slots = header["memory_slots"]
		if memory_slots > 0:
			program_head += "\n"
			if not classical_control_present:
				program_head += "ro = p.declare('ro', memory_type='BIT', memory_size=" + str(memory_slots) + ")\n"
			else:
				if memory_slots > 1:
					program_head += "sha_reg = p.declare('sha_reg', memory_type='INTEGER', memory_size=" + str(memory_slots) + ")\n"
					program_head += "int_reg = p.declare('int_reg', memory_type='INTEGER', memory_size=" + str(memory_slots) + ")\n"
					program_head += "ro = p.declare('ro', memory_type='BIT', memory_size=" + str(memory_slots) + ", shared_region='sha_reg')\n"
				else:
					program_head += "ro = p.declare('ro', memory_type='BIT', memory_size=" + str(memory_slots) + ")\n"

				program_head += "bit_reg = p.declare('bit_reg', memory_type='BIT', memory_size=1)\n"

	# 
	# Get number of qubits
	#
	if "n_qubits" in header:
		n_qubits = header["n_qubits"]

	conditions = {}

	for instruction in instructions:

		name = instruction["name"]

		if name == "bfunc":
			#
			# Classical condition
			#
			conditions[instruction["register"]] = { "mask": instruction["mask"], "val": instruction["val"] }

		elif name == "measure":
			for qindex in range(len(instruction["qubits"])):
				pyquil += "p += MEASURE(" + str(instruction["qubits"][qindex]) + ", ro[" + str(instruction["memory"][qindex]) + "])\n"

		elif name == "barrier":
			#
			# Barrier is not implemented
			#
			pass
		else:
			#
			# Regular gate
			#

			#
			# Find gateDef
			#
			if name not in gate_defs:
				raise Exception("Definition not found for gate \"" + name + "\".")

			gate_def = gate_defs[name]

			#
			# Find pyQuil exportInfo
			#
			if "exportInfo" not in gate_def:
				raise Exception("No export info for gate \"" + name + "\".")

			if "pyquil" not in gate_def["exportInfo"]:
				#
				# Quil exportInfo is enough
				#
				if "quil" not in gate_def["exportInfo"]:
					raise Exception("No pyQuil export info for gate \"" + name + "\".")
				else:
					pyquil_info = gate_def["exportInfo"]["quil"]
			else:
				pyquil_info = gate_def["exportInfo"]["pyquil"]

			user_defined_gate = False
			if "array" in pyquil_info and pyquil_info["array"] is not None and len(pyquil_info["array"]) > 0:
				#
				# User defined gate
				#
				user_defined_gate = True

				#
				# Already defined?
				#
				if name not in def_gate_names:
					#
					# def gate
					#
					if len(def_gate_names) == 0:
						imports += "from pyquil.quilatom import Parameter, quil_sin, quil_cos, quil_sqrt, quil_exp, quil_cis\n"
						imports += "from pyquil.quilbase import DefGate\n"
						imports += "import numpy as np\n"
					def_gate_names.append(name)

					param_list = ""
					if "params" in pyquil_info and pyquil_info["params"] is not None and len(pyquil_info["params"]) > 0:
						for param_name in pyquil_info["params"]:
							if param_name not in def_param_names:
								def_param_names.append(param_name) 
								def_params += "p_" + param_name + " = Parameter('" + param_name + "')\n"
								if param_list != "":
									param_list += ", "
								param_list += "p_" + param_name

					def_gates += name + "_matrix = np.array(" + pyquil_info["array"] + ")\n"

					decl_gates += name + "_defgate = DefGate('" + name + "', " + name + "_matrix, [" + param_list + "])\n"

					assign_gates += name  + " = " + name + "_defgate.get_constructor()\n"

					append_gates += "p += " + name + "_defgate"

			got_condition = False
			if "conditional" in instruction:
				#
				# Add classical condition
				#
				got_condition = True

				conditional = instruction["conditional"]

				condition = conditions[instruction["conditional"]]

				if memory_slots == 1:
					pyquil += "\n"
					pyquil += "p += MOVE(bit_reg, ro[" + str(condition["memory"]) + "])\n"
					if int(condition["val"]) == 0:
						pyquil += "NOT(bit_reg)"
					pyquil += "p.if_then(bit_reg, Program("
				else:
					pyquil += "\n"
					pyquil += "p += MOVE(int_reg, sha_reg)\n"
					pyquil += "p += AND(int_reg, " + condition["mask"] + ")\n"
					pyquil += "p += EQ(bit_reg, int_reg, " + condition["val"] + ")\n"
					pyquil += "p.if_then(bit_reg, Program("
			else:
				pyquil += "p += "

			#
			# Gate name
			#
			pyquil += pyquil_info["name"]
			pyquil += "("

			#
			# Gate params
			#
			param_count = 0
			if "params" in pyquil_info and len(pyquil_info["params"]) > 0:
				for param_name in gate_def["params"]:
					if param_name not in pyquil_info["params"]:
						raise Exception("Param \"" + param_name + "\" not found in pyQuil export info for gate \"" + name + "\".")

					param_index = pyquil_info["params"].index(param_name)
					if param_index >= len(instruction["params"]):
						raise Exception("Param \"" + param_name + "\" not specified in Qobj for gate \"" + name + "\".")

					if param_count > 0:
						pyquil += ", "
					param_count += 1

					pyquil += str(instruction["params"][param_index])

			if param_count > 0:
				if user_defined_gate:
					pyquil += ")("
				else:
					pyquil += ", "

			#
			# Target qubits
			#
			qubit_count = 0
			for qubit in instruction["qubits"]:
				if qubit_count > 0:
					pyquil += ", "
				qubit_count += 1
				pyquil += str(qubit)

			pyquil += ")"

			if got_condition:
				pyquil += "))\n"

			pyquil += "\n"

	#
	# Executable code
	#
	if "lattice" in options and options["lattice"] is not None and options["lattice"] != "qasm_simulator" and (options["lattice"].find("q-qvm") < 0):
		lattice_name = options["lattice"]

		#
		# Lattice name is given
		#
		if lattice_name == "statevector_simulator":
			#
			# Statevector
			#
			pyquil += "qc = WavefunctionSimulator()\n"
			if create_exec_code:
				pyquil += "\n"
				pyquil += "wf = qc.wavefunction(p)\n"
				pyquil += "print(wf)\n"
		else:
			#
			# QPU
			#

			#
			# Multishot?
			#
			if create_exec_code and "shots" in options and options["shots"] is not None and options["shots"] > 1:
				pyquil += "p.wrap_in_numshots_loop(" + str(options["shots"]) + ")\n"
				pyquil += "\n"

			#
			# get_qc
			#
			if "as_qvm" in options and options["as_qvm"]:
				pyquil += "qc = get_qc('" + lattice_name + "', as_qvm=True)\n"
			else:
				pyquil += "qc = get_qc('" + lattice_name + "')\n"

			#
			# Compile
			#
			pyquil += "\n"
			pyquil += "ex = qc.compile(p)\n"

			#
			# Run
			#
			if create_exec_code:
				pyquil += "print(qc.run(ex))\n"
	else:
		#
		# If lattice is not given or lattice name is "qasm_simulator"
		#
		if create_exec_code and "shots" in options and options["shots"] is not None and options["shots"] > 1:
			pyquil += "p.wrap_in_numshots_loop(" + str(options["shots"]) + ")\n"
			pyquil += "\n"

		#
		# get_qc
		#
		lattice_name = str(n_qubits) + "q-qvm"
		pyquil += "qc = get_qc('" + lattice_name + "')\n"

		#
		# Run
		#
		if create_exec_code:
			pyquil += "\n"
			pyquil += "print(qc.run(p))\n"
		else:
			pyquil += "ex = p\n"

	#
	# Assemble the code
	#
	code = ""
	code += imports
	code += "\n"

	if len(def_gate_names) > 0:
		code += def_params
		code += "\n"
		code += def_gates
		code += "\n"
		code += decl_gates
		code += "\n"
		code += assign_gates
		code += "\n"
		code += "\n"

	code += program_head
	code += "\n"

	if len(def_gate_names) > 0:
		code += append_gates
		code += "\n"
		code += "\n"

	code += pyquil

	return code


def qobj_to_pyquil(qobj, options = { "all_experiments": False, "create_exec_code": True, "lattice": None, "as_qvm": False }):
	pyquils = []

	if "experiments" not in qobj or len(qobj["experiments"]) == 0:
		return pyquil

	for experiment in qobj["experiments"]:
		pyquil = experiment_to_pyquil(experiment, options)
		pyquils.append(pyquil)

		if("all_experiments" not in options or options["all_experiments"] == False):
			return pyquils[0]

	return pyquils
