class QConvertBase:

	def __init__(self):
		self.clear()

	def clear(self):
		self.result = None
		self.results = []

	def convert(self, input_data, options={ "all_experiments": False }):
		self.clear()

		self.converter(input_data, options)

		all_experiments = False
		if options is not None and "all_experiments" in options and options["all_experiments"]:
			all_experiments = True

		if not all_experiments:
			return self.results[0]

		return self.results

	def on_start(self, data):
		pass

	def on_measure(self, data):
		pass

	def on_gate(self, data):
		pass

	def on_end(self, data):
		pass
