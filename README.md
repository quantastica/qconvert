# Quantum programming language converter

**Supported languages**

Python version of `quantastica-qconvert` currently supports only:

- `QOBJ` to `PYQUIL`

- `QOBJ` to `TOASTER`

More formats will be added soon.

Until then, for more formats see:

- JavaScript version as command line tool: [https://www.npmjs.com/package/q-convert](https://www.npmjs.com/package/q-convert)

- JavaScript version as online web page: [https://quantum-circuit.com/qconvert](https://quantum-circuit.com/qconvert)


# Usage:

```python

from quantastica.qconvert import convert

source_code = ...
options = {}

converted = convert(qconvert.Format.QOBJ,
                    source_code,
                    qconvert.Format.PYQUIL,
                    options)
print(converted)

```

More details soon.

Enjoy! :)
