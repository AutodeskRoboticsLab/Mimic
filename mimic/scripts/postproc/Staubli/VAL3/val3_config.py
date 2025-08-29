#!usr/bin/env python

"""
This module contains basic configuration parameters for SimpleVAL3Processor.
"""

# System parameters
DEFAULT_FILE_EXTENSION = 'pgx'

# Default program
DEFAULT_PROGRAM = \
	'<?xml version="1.0" encoding="utf-8"?>\n' \
	'<Programs xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.staubli.com/robotics/VAL3/Program/2">\n' \
	'  <Program name="main">\n' \
	'    <Code><![CDATA[begin\n' \
	'  close(tCurrentTool)\n' \
	'  pPointRx.config.shoulder = lefty\n' \
	'  pPointRx.config.elbow = epositive\n' \
	'  pPointRx.config.wrist = wpositive\n' \
	'  pPointRx2.config.shoulder = lefty\n' \
	'  pPointRx2.config.elbow = epositive\n' \
	'  pPointRx2.config.wrist = wpositive\n' \
	'  mCurrentSpeed.tvel = 100.00\n' \
	'  mCurrentSpeed.blend = joint\n' \
	'  mCurrentSpeed.reach = 0.010\n' \
	'  mCurrentSpeed.leave = 0.010\n' \
	'  // Program start\n' \
	'  mCurrentSpeed.tvel = 200.000\n' \
	'{}\n\n' \
	'  waitEndMove()\n' \
	'  // Program end\n\n' \
	'end]]></Code>\n' \
	'  </Program>\n' \
	'</Programs>\n'

