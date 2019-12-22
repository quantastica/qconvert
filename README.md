# Quantum programming language converter

Convert between quantum programming languages

More goodies at [https://quantastica.com](https://quantastica.com)


**Supported languages**

Python version of `quantastica-qconvert` currently supports only:

- Qobj to pyQuil

- Qobj to QubitToaster

More formats will be added soon.

Until then, for more formats see:

- JavaScript version as command line tool: [https://www.npmjs.com/package/q-convert](https://www.npmjs.com/package/q-convert)

- JavaScript version as online web page: [https://quantum-circuit.com/qconvert](https://quantum-circuit.com/qconvert)


# Usage

```python

from quantastica import qconvert

source_code = ...
options = {}

converted = qconvert.convert(qconvert.Format.QOBJ,
                    source_code,
                    qconvert.Format.PYQUIL,
                    options)
print(converted)

```

# Details

`convert(source_format, source_dict, dest_format, options)`

- `source_format` 

	- `Format.QOBJ`

- `dest_format`

	- `Format.PYQUIL`

	- `Format.TOASTER`



`options` Dict:

For all destination formats:

- `all_experiments` 
	- `False` (default) only first experiment will be converted and returned as string
	- `True` all experiments form Qobj will be converted and returned as list of strings. 

- `create_exec_code`
	- `True` (default) generated source code will contain command which executes circuit e.g. `qc.run()`

- `shots` (integer) if `create_exec_code` is `True` then generated code will perform `shots` number of samples


For `PYQUIL` destination:

- `lattice` name of the backend (e.g. for pyQuil destination `"Aspen-7-28Q-A"`). 
	- If ommited then "Nq-qvm" will be generated where `N` is number fo qubits in the circuit.
	- Special values:
		- `"qasm_simulator"` will produce "Nq-qvm" backend
		- `"statevector_simulator"` will produce WaveFunction simulator code

	- `as_qvm` (default `False`) if `True` QVM will mimic QPU specified by lattice argument.

For `TOASTER` destination:

*No options yet*


That's it. Enjoy! :)
