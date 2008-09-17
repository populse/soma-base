from soma.wip.application.api import Application
import sys

app = Application( 'soma', '1.0' )
app.initialize( sys.argv[ 1: ] )
