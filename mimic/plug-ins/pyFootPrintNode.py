#-
# ===========================================================================
# Copyright 2015 Autodesk, Inc.  All rights reserved.
#
# Use of this software is subject to the terms of the Autodesk license
# agreement provided at the time of installation or download, or which
# otherwise accompanies this software in either electronic or hard copy form.
# ===========================================================================
#+

########################################################################
# DESCRIPTION:
#
# Produces the dependency graph node "footPrint". 
#
# This example demonstrates how to create a user-defined locator. A locator
# is a DAG object that is drawn in 3D views, but does not render.
# This example plug-in defines a new locator node that draws a foot print.
# The foot print can be selected and moved using the regular manipulators. 
#
# To use, load the plug-in and execute:
#
#  maya.cmds.createNode('footPrint')
#
########################################################################

import sys
import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui
import maya.api.OpenMayaAnim as oma
import maya.api.OpenMayaRender as omr

def maya_useNewAPI():
	"""
	The presence of this function tells Maya that the plugin produces, and
	expects to be passed, objects created using the Maya Python API 2.0.
	"""
	pass

def matrixAsArray(matrix):
	array = []
	for i in range(16):
		array.append(matrix[i])
	return array

## Foot Data
##
sole = [ [  0.00, 0.0, -0.70 ],
				 [  0.04, 0.0, -0.69 ],
				 [  0.09, 0.0, -0.65 ],
				 [  0.13, 0.0, -0.61 ],
				 [  0.16, 0.0, -0.54 ],
				 [  0.17, 0.0, -0.46 ],
				 [  0.17, 0.0, -0.35 ],
				 [  0.16, 0.0, -0.25 ],
				 [  0.15, 0.0, -0.14 ],
				 [  0.13, 0.0,  0.00 ],
				 [  0.00, 0.0,  0.00 ],
				 [ -0.13, 0.0,  0.00 ],
				 [ -0.15, 0.0, -0.14 ],
				 [ -0.16, 0.0, -0.25 ],
				 [ -0.17, 0.0, -0.35 ],
				 [ -0.17, 0.0, -0.46 ],
				 [ -0.16, 0.0, -0.54 ],
				 [ -0.13, 0.0, -0.61 ],
				 [ -0.09, 0.0, -0.65 ],
				 [ -0.04, 0.0, -0.69 ],
				 [ -0.00, 0.0, -0.70 ] ]
heel = [ [  0.00, 0.0,  0.06 ],
				 [  0.13, 0.0,  0.06 ],
				 [  0.14, 0.0,  0.15 ],
				 [  0.14, 0.0,  0.21 ],
				 [  0.13, 0.0,  0.25 ],
				 [  0.11, 0.0,  0.28 ],
				 [  0.09, 0.0,  0.29 ],
				 [  0.04, 0.0,  0.30 ],
				 [  0.00, 0.0,  0.30 ],
				 [ -0.04, 0.0,  0.30 ],
				 [ -0.09, 0.0,  0.29 ],
				 [ -0.11, 0.0,  0.28 ],
				 [ -0.13, 0.0,  0.25 ],
				 [ -0.14, 0.0,  0.21 ],
				 [ -0.14, 0.0,  0.15 ],
				 [ -0.13, 0.0,  0.06 ],
				 [ -0.00, 0.0,  0.06 ] ]
soleCount = 21
heelCount = 17


#############################################################################
##
## Node implementation with standard viewport draw
##
#############################################################################
class footPrint(omui.MPxLocatorNode):
	id = om.MTypeId( 0x80007 )
	drawDbClassification = "drawdb/geometry/footPrint"
	drawRegistrantId = "FootprintNodePlugin"

	size = None	## The size of the foot

	@staticmethod
	def creator():
		return footPrint()

	@staticmethod
	def initialize():
		unitFn = om.MFnUnitAttribute()

		footPrint.size = unitFn.create( "size", "sz", om.MFnUnitAttribute.kDistance )
		unitFn.default = om.MDistance(1.0)

		om.MPxNode.addAttribute( footPrint.size )

	def __init__(self):
		omui.MPxLocatorNode.__init__(self)

	def compute(self, plug, data):
		return None

	def draw(self, view, path, style, status):
		## Get the size
		##
		thisNode = self.thisMObject()
		plug = om.MPlug( thisNode, footPrint.size )
		sizeVal = plug.asMDistance()
		multiplier = sizeVal.asCentimeters()

		global sole, soleCount
		global heel, heelCount

		view.beginGL()

		## drawing in VP1 views will be done using V1 Python APIs:
		import maya.OpenMayaRender as v1omr
		glRenderer = v1omr.MHardwareRenderer.theRenderer()
		glFT = glRenderer.glFunctionTable()

		if ( style == omui.M3dView.kFlatShaded ) or ( style == omui.M3dView.kGouraudShaded ):
			## Push the color settings
			##
			glFT.glPushAttrib( v1omr.MGL_CURRENT_BIT )

			# Show both faces
			glFT.glDisable( v1omr.MGL_CULL_FACE )

			if status == omui.M3dView.kActive:
				view.setDrawColor( 13, omui.M3dView.kActiveColors )
			else:
				view.setDrawColor( 13, omui.M3dView.kDormantColors )

			glFT.glBegin( v1omr.MGL_TRIANGLE_FAN )
			for i in range(soleCount-1):
				glFT.glVertex3f( sole[i][0] * multiplier, sole[i][1] * multiplier, sole[i][2] * multiplier )
			glFT.glEnd()

			glFT.glBegin( v1omr.MGL_TRIANGLE_FAN )
			for i in range(heelCount-1):
				glFT.glVertex3f( heel[i][0] * multiplier, heel[i][1] * multiplier, heel[i][2] * multiplier )
			glFT.glEnd()

			glFT.glPopAttrib()

		## Draw the outline of the foot
		##
		glFT.glBegin( v1omr.MGL_LINES )
		for i in range(soleCount-1):
			glFT.glVertex3f( sole[i][0] * multiplier, sole[i][1] * multiplier, sole[i][2] * multiplier )
			glFT.glVertex3f( sole[i+1][0] * multiplier, sole[i+1][1] * multiplier, sole[i+1][2] * multiplier )

		for i in range(heelCount-1):
			glFT.glVertex3f( heel[i][0] * multiplier, heel[i][1] * multiplier, heel[i][2] * multiplier )
			glFT.glVertex3f( heel[i+1][0] * multiplier, heel[i+1][1] * multiplier, heel[i+1][2] * multiplier )
		glFT.glEnd()

		view.endGL()

		## Draw the name of the footPrint
		view.setDrawColor( om.MColor( (0.1, 0.8, 0.8, 1.0) ) )
		view.drawText( "Footprint", om.MPoint( 0.0, 0.0, 0.0 ), omui.M3dView.kCenter )

	def isBounded(self):
		return True

	def boundingBox(self):
		## Get the size
		##
		thisNode = self.thisMObject()
		plug = om.MPlug( thisNode, footPrint.size )
		sizeVal = plug.asMDistance()
		multiplier = sizeVal.asCentimeters()

		corner1 = om.MPoint( -0.17, 0.0, -0.7 )
		corner2 = om.MPoint( 0.17, 0.0, 0.3 )

		corner1 *= multiplier
		corner2 *= multiplier

		return om.MBoundingBox( corner1, corner2 )
		
#############################################################################
##
## Viewport 2.0 override implementation
##
#############################################################################
class footPrintData(om.MUserData):
	def __init__(self):
		om.MUserData.__init__(self, False) ## don't delete after draw

		self.fColor = om.MColor()
		self.fLineList = om.MPointArray()
		self.fTriangleList = om.MPointArray()

class footPrintDrawOverride(omr.MPxDrawOverride):
	@staticmethod
	def creator(obj):
		return footPrintDrawOverride(obj)

	## By setting isAlwaysDirty to false in MPxDrawOverride constructor, the
	## draw override will be updated (via prepareForDraw()) only when the node
	## is marked dirty via DG evaluation or dirty propagation. Additional
	## callback is also added to explicitly mark the node as being dirty (via
	## MRenderer::setGeometryDrawDirty()) for certain circumstances. 
	def __init__(self, obj):
		omr.MPxDrawOverride.__init__(self, obj, None, False)

		## We want to perform custom bounding box drawing
		## so return True so that the internal rendering code
		## will not draw it for us.
		self.mCustomBoxDraw = True
		self.mCurrentBoundingBox = om.MBoundingBox()

	def supportedDrawAPIs(self):
		## this plugin supports both GL and DX
		return omr.MRenderer.kOpenGL | omr.MRenderer.kDirectX11 | omr.MRenderer.kOpenGLCoreProfile

	def isBounded(self, objPath, cameraPath):
		return True

	def boundingBox(self, objPath, cameraPath):
		corner1 = om.MPoint( -0.17, 0.0, -0.7 )
		corner2 = om.MPoint( 0.17, 0.0, 0.3 )

		multiplier = self.getMultiplier(objPath)
		corner1 *= multiplier
		corner2 *= multiplier

		self.mCurrentBoundingBox.clear()
		self.mCurrentBoundingBox.expand( corner1 )
		self.mCurrentBoundingBox.expand( corner2 )

		return self.mCurrentBoundingBox

	def disableInternalBoundingBoxDraw(self):
		return self.mCustomBoxDraw

	def prepareForDraw(self, objPath, cameraPath, frameContext, oldData):
		## Retrieve data cache (create if does not exist)
		data = oldData
		if not isinstance(data, footPrintData):
			data = footPrintData()

		## compute data and cache it
		global soleCount, sole
		global heelCount, heel

		fMultiplier = self.getMultiplier(objPath)

		data.fLineList.clear()

		for i in range(soleCount-1):
			data.fLineList.append( om.MPoint(sole[i][0] * fMultiplier, sole[i][1] * fMultiplier, sole[i][2] * fMultiplier) )
			data.fLineList.append( om.MPoint(sole[i+1][0] * fMultiplier, sole[i+1][1] * fMultiplier, sole[i+1][2] * fMultiplier) )

		for i in range(heelCount-1):
			data.fLineList.append( om.MPoint(heel[i][0] * fMultiplier, heel[i][1] * fMultiplier, heel[i][2] * fMultiplier) )
			data.fLineList.append( om.MPoint(heel[i+1][0] * fMultiplier, heel[i+1][1] * fMultiplier, heel[i+1][2] * fMultiplier) )

		data.fTriangleList.clear()

		for i in range(1,soleCount-1):
			data.fTriangleList.append( om.MPoint(sole[0][0] * fMultiplier, sole[0][1] * fMultiplier, sole[0][2] * fMultiplier) )
			data.fTriangleList.append( om.MPoint(sole[i][0] * fMultiplier, sole[i][1] * fMultiplier, sole[i][2] * fMultiplier) )
			data.fTriangleList.append( om.MPoint(sole[i+1][0] * fMultiplier, sole[i+1][1] * fMultiplier, sole[i+1][2] * fMultiplier) )

		for i in range(1,heelCount-1):
			data.fTriangleList.append( om.MPoint(heel[0][0] * fMultiplier, heel[0][1] * fMultiplier, heel[0][2] * fMultiplier) )
			data.fTriangleList.append( om.MPoint(heel[i][0] * fMultiplier, heel[i][1] * fMultiplier, heel[i][2] * fMultiplier) )
			data.fTriangleList.append( om.MPoint(heel[i+1][0] * fMultiplier, heel[i+1][1] * fMultiplier, heel[i+1][2] * fMultiplier) )

		data.fColor = omr.MGeometryUtilities.wireframeColor(objPath)

		return data

	def hasUIDrawables(self):
		return True

	def addUIDrawables(self, objPath, drawManager, frameContext, data):
		locatordata = data
		if not isinstance(locatordata, footPrintData):
			return

		drawManager.beginDrawable()
		
		##Draw the foot print solid/wireframe
		drawManager.setColor( locatordata.fColor )
		drawManager.setDepthPriority(5)

		if (frameContext.getDisplayStyle() & omr.MFrameContext.kGouraudShaded):
			drawManager.mesh(omr.MGeometry.kTriangles, locatordata.fTriangleList)
			
		drawManager.mesh(omr.MUIDrawManager.kLines, locatordata.fLineList)

		## Draw a text "Foot"
		pos = om.MPoint( 0.0, 0.0, 0.0 )  ## Position of the text
		textColor = om.MColor( (0.1, 0.8, 0.8, 1.0) )  ## Text color

		drawManager.setColor( textColor )
		drawManager.setFontSize( omr.MUIDrawManager.kSmallFontSize )
		drawManager.text(pos, "Footprint", omr.MUIDrawManager.kCenter )

		drawManager.endDrawable()

	def getMultiplier(self, objPath):
		## Retrieve value of the size attribute from the node
		footprintNode = objPath.node()
		plug = om.MPlug(footprintNode, footPrint.size)
		if not plug.isNull:
			sizeVal = plug.asMDistance()
			return sizeVal.asCentimeters()

		return 1.0

def initializePlugin(obj):
	plugin = om.MFnPlugin(obj, "Autodesk", "3.0", "Any")

	try:
		plugin.registerNode("footPrint", footPrint.id, footPrint.creator, footPrint.initialize, om.MPxNode.kLocatorNode, footPrint.drawDbClassification)
	except:
		sys.stderr.write("Failed to register node\n")
		raise

	try:
		omr.MDrawRegistry.registerDrawOverrideCreator(footPrint.drawDbClassification, footPrint.drawRegistrantId, footPrintDrawOverride.creator)
	except:
		sys.stderr.write("Failed to register override\n")
		raise

def uninitializePlugin(obj):
	plugin = om.MFnPlugin(obj)

	try:
		plugin.deregisterNode(footPrint.id)
	except:
		sys.stderr.write("Failed to deregister node\n")
		pass

	try:
		omr.MDrawRegistry.deregisterDrawOverrideCreator(footPrint.drawDbClassification, footPrint.drawRegistrantId)
	except:
		sys.stderr.write("Failed to deregister override\n")
		pass

