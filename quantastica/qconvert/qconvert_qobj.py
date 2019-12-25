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


from .qconvert_base import QConvertBase, gate_defs, eval_mathjs_matrix


class QConvertQobj(QConvertBase):

	def converter(self, qobj, options = { "all_experiments": False }):

		all_experiments = False
		if self.options is not None and "all_experiments" in self.options and self.options["all_experiments"]:
			all_experiments = True

		if "experiments" not in qobj or len(qobj["experiments"]) == 0:
			if all_experiments:
				return []
			else:
				return None

		for experiment in qobj["experiments"]:
			self.result = None
			self.experiment_converter(experiment)
			self.results.append(self.result)

			if not all_experiments:
				return

	def experiment_converter(self, experiment):

		#
		# Do we have header in Qobj?
		#
		if "header" not in experiment:
			raise Exception("Qobj header not found.")

		header = experiment["header"]
		instructions = experiment["instructions"]

		info = {	"return_state_vector": False,
					"create_exec_code": False,
					"classical_control_present": False,
					"qubits": 0,
					"memory_slots": 0,
					"cregs": {} }

		#
		# Does user requests state vector?
		#
		if self.options is not None and "lattice" in self.options and self.options["lattice"] == "statevector_simulator":
			info["return_state_vector"] = True

		#
		# Does user want to generate executable code?
		#
		create_exec_code = False
		if self.options is not None and ("create_exec_code" not in self.options or self.options["create_exec_code"]):
			info["create_exec_code"] = True

		classical_control_present = False
		for instruction in instructions:
			if instruction["name"] == "bfunc":
				info["classical_control_present"] = True
				break

		#
		# Get classical registers
		#
		if "memory_slots" in header:
			info["memory_slots"] = header["memory_slots"]


		creg_masks = {}
		if "creg_sizes" in header:
			total_bits = 0
			for creg_data in header["creg_sizes"]:
				if len(creg_data) >= 2:
					creg_name = creg_data[0]
					creg_len = creg_data[1]
					creg_mask = (1 << (total_bits + creg_len)) - (1 << total_bits)
					creg_val_offset = (1 << total_bits) - 1
					info["cregs"][creg_name] = {	"memory_offset": total_bits,
													"len": creg_len,
													"mask": creg_mask }

					creg_masks[str(creg_mask)] = {	"memory_offset": total_bits,
													"name": creg_name }

					total_bits += creg_len

		# 
		# Get number of qubits
		#
		if "n_qubits" in header:
			info["qubits"] = header["n_qubits"]

		self.on_start({	"experiment": experiment,
						"info": info })

		conditions = {}

		for instruction in instructions:

			self.on_qobj_instruction({ "instruction": instruction, "info": info })

			name = ""
			if "name" in instruction:
				name = instruction["name"]

			#
			# Translate gate names to gate_defs
			#
			if name == "iden":
				name = "id"

			if name == "bfunc":
				#
				# Classical condition
				#
				bfunc_mask = int(instruction["mask"], 0)
				bfunc_val = int(instruction["val"], 0)
				if not str(bfunc_mask) in creg_masks:
					raise Exception("Cannot find classical register by mask in bfunc")

				bfunc_relation = None
				if("relation" in instruction):
					bfunc_relation = instruction["relation"]

				bfunc_creg = creg_masks[str(bfunc_mask)]

				conditions[instruction["register"]] = { "mask": bfunc_mask,
														"val": bfunc_val,
														"memory": bfunc_creg["memory_offset"],
														"relation": bfunc_relation,
														"creg_name": bfunc_creg["name"],
														"creg_value": bfunc_val >> bfunc_creg["memory_offset"] }

			elif name == "measure":
				for qindex in range(len(instruction["qubits"])):
					memory = instruction["memory"][qindex]
					qubit = instruction["qubits"][qindex]
					dest_creg_name = None
					dest_bit = None

					total_bits = 0
					for creg_name in info["cregs"]:
						creg_info = info["cregs"][creg_name]
						if (total_bits + creg_info["len"]) > memory:
							dest_creg_name = creg_name
							dest_bit = memory - total_bits
							break
						total_bits += creg_info["len"]

					self.on_measure({	"qubit": qubit,
										"creg_name": dest_creg_name,
										"creg_bit": dest_bit,
										"memory": memory,
										"info": info })

			elif name == "barrier":
				#
				# Barrier
				#
				self.on_barrier({	"info": info })

				pass
			else:
				#
				# Regular gate
				#

				#
				# Find gateDef
				#
				params = None
				if "params" in instruction:
					params = instruction["params"]

				gate_def = None
				params_dict = {}
				matrix = None
				if name in gate_defs:
					gate_def = gate_defs[name]

					if "params" in gate_def:
						param_index = 0
						for param_name in gate_def["params"]:
							params_dict[param_name] = params[param_index]
							param_index += 1

					if "matrix" in gate_def:
						matrix = eval_mathjs_matrix(gate_def["matrix"], params_dict)


				condition = None
				if "conditional" in instruction:
					#
					# Add classical condition
					#
					condition = conditions[instruction["conditional"]]


				qubits = []
				if "qubits" in instruction:
					qubits = instruction["qubits"]

				self.on_gate({	"name": name,
								"gate_def": gate_def,
								"condition": condition,
								"params": params,
								"params_dict": params_dict,
								"qubits": qubits,
								"matrix": matrix,
								"info": info })

		self.on_end({	"experiment": experiment,
						"info": info })



	def on_qobj_instruction(self, data):
		pass
