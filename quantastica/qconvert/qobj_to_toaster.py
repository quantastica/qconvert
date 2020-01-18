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

from .qconvert_base import gate_defs
from .qconvert_qobj import QConvertQobj
import json

class QobjToToaster(QConvertQobj):

	def on_start(self, data):
		info = data["info"]

		self.result = {}
		self.result["qubits"] = info["qubits"]
		self.result["cregs"] = []
		self.result["program"] = []

		for creg_name in info["cregs"]:
			creg_info = info["cregs"][creg_name]
			self.result["cregs"].append({ "name": creg_name, "len": creg_info["len"] })

	def on_measure(self, data):
		gate = {}
		gate["name"] = "measure"
		gate["wires"] = []
		gate["wires"].append(data["qubit"])
		gate["options"] = {}
		gate["matrix"] = []

		creg = {}
		creg["bit"] = data["creg_bit"]
		creg["name"] = data["creg_name"]
		gate["options"]["creg"] = creg

		self.result["program"].append(gate)

		return

	def on_gate(self, data):
		if data["gate_def"] is None:
			raise Exception("Definition not found for gate \"" + data["name"] + "\".")

		gate = {}
		gate["name"] = data["name"]
		gate["wires"] = data["qubits"]
		gate["options"] = {}
		gate["matrix"] = []

		if "matrix" in data and data["matrix"] is not None:
			gate["matrix"] = data["matrix"]

		if data["condition"] is not None:
			condition = {}
			condition["creg"] = data["condition"]["creg_name"]
			condition["value"] = data["condition"]["creg_value"]

			gate["options"]["condition"] = condition

		self.result["program"].append(gate)


	def on_end(self, data):
		if type(self.result) is dict:
			self.result = json.dumps(self.result)
		return


def qobj_to_toaster(qobj, options):
	converter = QobjToToaster()

	toast = converter.convert(qobj, options)

	return toast
