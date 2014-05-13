# This module is used to call a Process or a Pipeline from the command line 
# with: "python -m soma.pipeline <process_id> [<parameter>...]" where 
# <parameter> can be a value or <parameter name>=<value>.

import sys
from capsul.pipeline.process import Process

process = Process.get_instance( sys.argv[ 1 ] )
process.set_string_list( sys.argv[ 2: ] )
process()


