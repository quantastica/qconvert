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

from enum import Enum
from . import qobj_to_pyquil, qobj_to_toaster
from . import qconvert_base

class Format(Enum):
    UNDEFINED = 0
    QOBJ = 1
    PYQUIL = 2
    TOASTER = 3

# Options:
# - PYQUIL:
#   all_experiments: - True: all experiments form Qobj will be converted and returned as list of strings. 
#                    - False (default): only first experiment will be converted and returned as string
#
#   create_exec_code: if True: print(qc.run(ex)) will be created. Default: True
#
#   lattice: name of the backend lattice (e.g. "Aspen-7-28Q-A"). If ommited then "Nq-qvm" will be generated
#               - special values: - "qasm_simulator" will produce "Nq-qvm" backend
#                                 - "statevector_simulator" will produce WaveFunction simulator code
#
#   as_qvm: True/False. if True, QVM will mimic QPU specified by lattice argument. Default: False
#   seed: if valid integer set random_seed for qc.qam to given value. Default: None 
# - TOASTER: ...

def convert(source_format, source_dict, dest_format, options = dict() ):
    ret = None

    if source_format == Format.QOBJ: 
        if dest_format == Format.PYQUIL:
            ret = qobj_to_pyquil.qobj_to_pyquil(source_dict, options)
        elif dest_format == Format.TOASTER:
            ret = qobj_to_toaster.qobj_to_toaster(source_dict, options)
        else:
            msg = "Unsuported conversion formats - source: %s  destination: %s"%(str(source_format),str(dest_format))
            raise RuntimeError(msg)
    else:
        msg = "Unsuported conversion formats - source: %s  destination: %s"%(str(source_format),str(dest_format))
        raise RuntimeError(msg)

    return ret

def supported_gates():
    return list(qconvert_base.gate_defs.keys())
