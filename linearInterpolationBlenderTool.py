bl_info = {  
 "name": "Linear Interpolation Blender Tool",  
 "author": "Boris Musarais (MrNothing)",  
 "version": (1, 0),  
 "blender": (2, 6, 4),  
 "location": "",  
 "description": "This solution provides tools to procedurally generate meshes using Linear Interpolation.",  
 "warning": "",  
 "wiki_url": "https://github.com/MrNothing/Linear-Interpolation-Blender-Tool/wiki",  
 "tracker_url": "",  
 "category": "Object"}  

import bpy
import bmesh
import math
import mathutils
import warnings
from bpy.props import*
from mathutils import Vector

#the selected Objects used as reference for the interpolation
bpy.interpolationMeshes = []

#the object generated after the interpolation
bpy.generatedMeshResult = 0

#the linear interpolant for each selected Object
bpy.types.Object.interpolationRate = FloatProperty(
    name="interpolationRate", 
    min = 0, max = 1,
    default = 0)

#the active mesh index the brush will use as a reference
bpy.interpolationBrushIndex = 0

#the size of the brush in the scene
bpy.types.Object.interpolationBrushSize = FloatProperty(
    name="interpolationBrushSize", 
    min = 0, max = 10,
    default = 0)

#the intensity of the brush
bpy.types.Object.interpolationBrushIntensity = FloatProperty(
    name="interpolationBrushIntensity", 
    min = 0, max = 1,
    default = 0)
	
"""Main Pannel"""	
class LinearInterpolation(bpy.types.Panel):
	bl_label = "Linear Interpolation Manager"
	bl_idname = "OBJECT_PT_LinearInterpolation"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'TOOL_PROPS'
	
	def draw(self, context):
		layout = self.layout

		obj = context.object
		
		row = layout.row()
		row.label(text="Objects", icon='WORLD_DATA')
		row.operator("object.interpolateremovemesh")
		
		for tmpObj in bpy.interpolationMeshes:
			row = layout.row()
			row.label(text="list: "+tmpObj.name)
		
		#row = layout.row()
		#row.label(text=str(bpy.interpolationMeshes))
		
		#row = layout.row()
		#row.operator("object.interpolate")
		
		row = layout.row()
		row.operator("object.testbmesh")
		
		row = layout.row()
		row.label("Paint tool")
		
		try:
			test = bpy.generatedMeshResult.data
			if(len(bpy.interpolationMeshes)==0):
				row = layout.row()
				row.label("You must generate a mesh to use the paint tool.")
				return None
		except:
			row = layout.row()
			row.label("You must generate a mesh to use the paint tool.")
			return None
		
		row = layout.row()
		row.operator("object.decrementbrushindex")
		row.label(bpy.interpolationMeshes[bpy.interpolationBrushIndex].name)
		row.operator("object.incrementbrushindex")
		
		row = layout.row()
		layout.prop(bpy.generatedMeshResult, 'interpolationBrushIntensity', 'Brush intensity')
		
		row = layout.row()
		layout.prop(bpy.generatedMeshResult, 'interpolationBrushSize', 'Brush size')
		
		row = layout.row()
		row.operator("object.applyinterpolationbrush");
		row.label("uses the 3D cursor")
		
"""Inspector"""
class LinearInterpolationInspector(bpy.types.Panel):
	bl_label = "Linear Interpolation Inspector"
	bl_idname = "OBJECT_PT_LinearInterpolationPannel"
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "object"
	
	def draw(self, context):
		layout = self.layout

		obj = context.object
		
		row = layout.row()
		row.label(text="Selected: " + obj.name)
		row.operator("object.interpolateaddmesh")
		
		row = layout.row()
		layout.prop(obj, 'interpolationRate', "Interpolation level")

"""Add Button"""
class InterpolateAddMesh(bpy.types.Operator):
	bl_idname = "object.interpolateaddmesh"
	bl_label="Add selected object"
	
	def execute(self, context):
		if(bpy.interpolationMeshes.count(context.object)==0):
			print("added object: "+context.object.name+" to the list")
			bpy.interpolationMeshes.append(context.object)
		else:
			self.report({'INFO'}, 'object: '+context.object.name+' was already in the list!')
			
		return {'FINISHED'}

"""Reset Button"""
class InterpolateResetMesh(bpy.types.Operator):
	bl_idname = "object.interpolateremovemesh"
	bl_label="Reset All Meshes"
	
	def execute(self, context):
		try:
			bpy.context.scene.objects.unlink(bpy.generatedMeshResult)
		except :
			self.report({'INFO'}, 'nothing to delete, proceeding...')
		bpy.interpolationMeshes = []
		bpy.interpolationBrushIndex = 0
		return {'FINISHED'}
		
"""Increment the Brush's selected index"""
class IncrementBrushIndex(bpy.types.Operator):
	bl_idname = "object.incrementbrushindex"
	bl_label="next"
	
	def execute(self, context):
		if(bpy.interpolationBrushIndex<len(bpy.interpolationMeshes)-1):
			bpy.interpolationBrushIndex+=1
		return {'FINISHED'}
		
"""Increment the Brush's selected index"""
class DecrementBrushIndex(bpy.types.Operator):
	bl_idname = "object.decrementbrushindex"
	bl_label="previous"
	
	def execute(self, context):
		if(bpy.interpolationBrushIndex>0):
			bpy.interpolationBrushIndex-=1
		return {'FINISHED'}

"""Interpolation technique (DEPRECATED: this method does not handle UVs, use InterpolateNew instead)"""
class Interpolate(bpy.types.Operator):
	bl_idname = "object.interpolate"
	bl_label="Interpolate!"
	
	def execute(self, context):
	
		if(len(bpy.interpolationMeshes)<2):
			self.report({'WARNING'}, 'At least two meshes must be selected!')
			return {'FINISHED'}
		
		try:
			bpy.context.scene.objects.unlink(bpy.generatedMeshResult)
		except :
			self.report({'INFO'}, 'nothing to delete, proceeding...')
		reCalculatedVertices = []
		clonedFaces = []
		
		totalInterpolationsMessageSent = 0
		
		for vert in bpy.interpolationMeshes[0].data.vertices:
			recalculatesVertice = [0, 0, 0]
			totalInterpolations = 0
			for mesh in bpy.interpolationMeshes:
				recalculatesVertice[0] += mesh.data.vertices[vert.index].co.x*mesh.interpolationRate
				recalculatesVertice[1] += mesh.data.vertices[vert.index].co.y*mesh.interpolationRate
				recalculatesVertice[2] += mesh.data.vertices[vert.index].co.z*mesh.interpolationRate
				totalInterpolations+=mesh.interpolationRate
			
			if(totalInterpolations<1):
				if(totalInterpolationsMessageSent == 0):
					totalInterpolationsMessageSent = 1
					self.report({'WARNING'}, 'interpolation rates are under 1, the mesh will be smaller!')
				totalInterpolations = 1		
				
			recalculatesVertice[0]/=totalInterpolations
			recalculatesVertice[1]/=totalInterpolations
			recalculatesVertice[2]/=totalInterpolations
			
			reCalculatedVertices.append(recalculatesVertice)
			
		for polygon in context.object.data.polygons:
			verts_in_face = polygon.vertices[:]  
			tmpFace = []
			for vert in verts_in_face:
				tmpFace.append(vert)
			clonedFaces.append(tmpFace)
			
		#print("reCalculatedVertices: "+str(len(reCalculatedVertices)))
		#print("polygons: "+str(len(clonedFaces)))
		
		bpy.generatedMeshResult = createMeshFromData("test",  Vector((0, 0, 0)), reCalculatedVertices, clonedFaces)
		
		#bpy.generatedMeshResult.data.tessface_uv_textures = bpy.interpolationMeshes[0].data.tessface_uv_textures
		
		return {'FINISHED'}
		
"""Interpolation technique: Clones and creates the mesh using BMesh"""
class InterpolateWithBmesh(bpy.types.Operator):
	bl_idname = "object.testbmesh"
	bl_label="Generate!"
	
	def execute(self, context):
	
		if(len(bpy.interpolationMeshes)<2):
			self.report({'WARNING'}, 'At least two meshes must be selected!')
			return {'FINISHED'}
		
		hasToClone = 0
		try:
			test = bpy.generatedMeshResult.data.vertices
			self.report({'INFO'}, 'mesh already exists proceeding...')
		except :
			hasToClone = 1
			self.report({'INFO'}, 'mesh not found, cloning it...')
		
		reCalculatedVertices = []
		clonedFaces = []
		
		totalInterpolationsMessageSent = 0
		
		# Get the active mesh
		if(hasToClone==1):
			bpy.generatedMeshResult = duplicateObject("generated", bpy.interpolationMeshes[0])
		
		# Get a BMesh representation
		bm = bmesh.new()   # create an empty BMesh
		bm.from_mesh(bpy.generatedMeshResult.data)   # fill it in from a Mesh

		for vert in bpy.interpolationMeshes[0].data.vertices:
			recalculatesVertice = [0, 0, 0]
			totalInterpolations = 0
			for mesh in bpy.interpolationMeshes:
				recalculatesVertice[0] += mesh.data.vertices[vert.index].co.x*mesh.interpolationRate
				recalculatesVertice[1] += mesh.data.vertices[vert.index].co.y*mesh.interpolationRate
				recalculatesVertice[2] += mesh.data.vertices[vert.index].co.z*mesh.interpolationRate
				totalInterpolations+=mesh.interpolationRate
			
			if(totalInterpolations<1):
				if(totalInterpolationsMessageSent == 0):
					totalInterpolationsMessageSent = 1
					self.report({'WARNING'}, 'interpolation rates are under 1, the mesh will be smaller!')
				totalInterpolations = 1		
				
			recalculatesVertice[0]/=totalInterpolations
			recalculatesVertice[1]/=totalInterpolations
			recalculatesVertice[2]/=totalInterpolations
			
			bm.verts[vert.index].co.x = recalculatesVertice[0]
			bm.verts[vert.index].co.y = recalculatesVertice[1]
			bm.verts[vert.index].co.z = recalculatesVertice[2]
		
		# Finish up, write the bmesh back to the mesh
		bm.to_mesh(bpy.generatedMeshResult.data)
		bm.free()  # free and prevent further access
		return {'FINISHED'}
		
"""Interpolation technique: modifies the mesh using bmesh"""
"""Takes the brush mesh, position and size in account"""
def applyBrush(self, brushPosition):
	allowProceed = 1
	try:
		test = bpy.generatedMeshResult.data.vertices
		self.report({'INFO'}, 'mesh exists proceeding...')
	except :
		self.report({'ERROR'}, 'No mesh generated, please generate a mesh using the "Interpolate" button first')
		allowProceed = 0
			
	if(bpy.generatedMeshResult.interpolationBrushSize<=0):
		self.report({'WARNING'}, 'Bush size is set to 0, this will do nothing!')
		allowProceed = 0
	
	if(bpy.generatedMeshResult.interpolationBrushIntensity<=0):
		self.report({'WARNING'}, 'Bush intensity is set to 0, this will do nothing!')
		allowProceed = 0
	
	if(allowProceed==1):
		reCalculatedVertices = []
		clonedFaces = []
		
		totalInterpolationsMessageSent = 0
		
		# Get a BMesh representation
		bm = bmesh.new()   # create an empty BMesh
		bm.from_mesh(bpy.generatedMeshResult.data)   # fill it in from a Mesh
		
		#the position of the reference mesh
		meshPosition = bpy.generatedMeshResult.location
		
		refrenceMesh = bpy.interpolationMeshes[bpy.interpolationBrushIndex]
		
		for vert in bpy.generatedMeshResult.data.vertices:
			recalculatesVertice = [vert.co.x, vert.co.y, vert.co.z]
			
			#print("ABS: "+str(abs(recalculatesVertice[0]-refrenceMesh.data.vertices[vert.index].co.x)))
			#print("bpy.interpolationBrushIntensity: "+str(bpy.generatedMeshResult.interpolationBrushIntensity))
			
			vertWorldPosition = meshPosition+Vector((vert.co.x, vert.co.y, vert.co.z))
					
			distance = getDistance(vertWorldPosition, brushPosition)
			relativeIntensity = (1-distance/bpy.generatedMeshResult.interpolationBrushSize)
			
			if(relativeIntensity>1):
				relativeIntensity = 1
			
			try:
			
				if(relativeIntensity>0): #if i am in brush range
				
					if(recalculatesVertice[0]>refrenceMesh.data.vertices[vert.index].co.x):
						recalculatesVertice[0]-=abs(recalculatesVertice[0]-refrenceMesh.data.vertices[vert.index].co.x)*bpy.generatedMeshResult.interpolationBrushIntensity*relativeIntensity
					
					if(recalculatesVertice[0]<refrenceMesh.data.vertices[vert.index].co.x):
						recalculatesVertice[0]+=abs(recalculatesVertice[0]-refrenceMesh.data.vertices[vert.index].co.x)*bpy.generatedMeshResult.interpolationBrushIntensity*relativeIntensity
						
					if(recalculatesVertice[1]>refrenceMesh.data.vertices[vert.index].co.y):
						recalculatesVertice[1]-=abs(recalculatesVertice[1]-refrenceMesh.data.vertices[vert.index].co.y)*bpy.generatedMeshResult.interpolationBrushIntensity*relativeIntensity
					
					if(recalculatesVertice[1]<refrenceMesh.data.vertices[vert.index].co.y):
						recalculatesVertice[1]+=abs(recalculatesVertice[1]-refrenceMesh.data.vertices[vert.index].co.y)*bpy.generatedMeshResult.interpolationBrushIntensity*relativeIntensity
						
					if(recalculatesVertice[2]>refrenceMesh.data.vertices[vert.index].co.z):
						recalculatesVertice[2]-=abs(recalculatesVertice[2]-refrenceMesh.data.vertices[vert.index].co.z)*bpy.generatedMeshResult.interpolationBrushIntensity*relativeIntensity
					
					if(recalculatesVertice[2]<refrenceMesh.data.vertices[vert.index].co.z):
						recalculatesVertice[2]+=abs(recalculatesVertice[2]-refrenceMesh.data.vertices[vert.index].co.z)*bpy.generatedMeshResult.interpolationBrushIntensity*relativeIntensity
			
				bm.verts[vert.index].co.x = recalculatesVertice[0]
				bm.verts[vert.index].co.y = recalculatesVertice[1]
				bm.verts[vert.index].co.z = recalculatesVertice[2]
			except :
				allowProceed -= 1
		
		if(allowProceed <= 0):
			self.report({'WARNING'}, str(allowProceed-1)+' vertices were not cloned! Make sure all reference Meshes share the same amount of vertices!')
		
		# Finish up, write the bmesh back to the mesh
		bm.to_mesh(bpy.generatedMeshResult.data)
		bm.free()  # free and prevent further access
	

"""Simple operator to get the mouse position"""
class SimpleMouseOperator(bpy.types.Operator):
	bl_idname = "wm.mouse_position"
	bl_label = "Show mouse position"

	x = bpy.props.IntProperty()
	y = bpy.props.IntProperty()

	def execute(self, context):
	
		self.report({'INFO'}, "Mouse coords are %d %d" % (self.x, self.y))
		return {'FINISHED'}

	def invoke(self, context, event):
	
		self.x = event.mouse_x
		self.y = event.mouse_y
		return self.execute(context)

"""used to call the applyBrush function"""
class InterpolationBrushOperator(bpy.types.Operator):
	bl_idname = "object.applyinterpolationbrush"
	bl_label="Apply Brush!"
	
	def execute(self, context):
		applyBrush(self, bpy.context.scene.cursor_location)
		return {'FINISHED'}
	
"""Operator that handles events and shows mouse position"""
class ModalOperator(bpy.types.Operator):
	bl_idname = "object.modal_operator"
	bl_label = "Apply Brush"

	x = 0
	y = 0
	
	def __init__(self):
		self.report({'INFO'}, "Brush Interpolation Enabled")

	def __del__(self):
		self.report({'INFO'}, "Brush Interpolation Disabled")

	def execute(self, context):
		self.report({'INFO'}, "Mouse coords are %d %d" % (self.x, self.y))

	def modal(self, context, event):
		#if event.type == 'MOUSEMOVE':  # Apply
            #do nothing for now
		if event.type == 'LEFTMOUSE':  # Apply and finish
			#do nothing for now
			return {'FINISHED'}
		elif event.type in ('RIGHTMOUSE', 'ESC'):  # Cancel
			return {'CANCELLED'}

		return {'RUNNING_MODAL'}

	def invoke(self, context, event):
		self.x = event.mouse_x
		self.y = event.mouse_y
		self.execute(context)

		print(context.window_manager.modal_handler_add(self))
		return {'RUNNING_MODAL'}
		
"""Mesh creation function"""
def createMeshFromData(name, origin, verts, faces):
    # Create mesh and object
    me = bpy.data.meshes.new(name+'_generated')
    ob = bpy.data.objects.new(name, me)
    ob.location = origin
    ob.show_name = True
 
    # Link object to scene and make active
    scn = bpy.context.scene
    scn.objects.link(ob)
    scn.objects.active = ob
    ob.select = True
 
    # Create mesh from given verts, faces.
    me.from_pydata(verts, [], faces)
    # Update mesh with new data
    me.update()    
    return ob	
	
"""Simple function to duplicate an Object"""
def duplicateObject(name, copyobj):
 
    # Create new mesh
    mesh = bpy.data.meshes.new(name)
 
    # Create new object associated with the mesh
    ob_new = bpy.data.objects.new(name, mesh)
 
    # Copy data block from the old object into the new object
    ob_new.data = copyobj.data.copy()
    ob_new.scale = copyobj.scale
    ob_new.location = Vector((0, 0, 0))
 
    # Link new object to the given scene and select it
    bpy.context.scene.objects.link(ob_new)
    ob_new.select = True
 
    return ob_new
	
def getDistance(vectorA, vectorB):
	rawDistance =(vectorB.x-vectorA.x)*(vectorB.x-vectorA.x)+(vectorB.y-vectorA.y)*(vectorB.y-vectorA.y)+(vectorB.z-vectorA.z)*(vectorB.z-vectorA.z)
	return math.sqrt(rawDistance)

def register():
	bpy.utils.register_class(LinearInterpolation)
	bpy.utils.register_class(LinearInterpolationInspector)
	bpy.utils.register_class(Interpolate)
	bpy.utils.register_class(InterpolateResetMesh)
	bpy.utils.register_class(InterpolateAddMesh)
	bpy.utils.register_class(InterpolateWithBmesh)
	bpy.utils.register_class(SimpleMouseOperator)
	bpy.utils.register_class(ModalOperator)
	bpy.utils.register_class(IncrementBrushIndex)
	bpy.utils.register_class(DecrementBrushIndex)
	bpy.utils.register_class(InterpolationBrushOperator)

def unregister():
	bpy.utils.unregister_class(LinearInterpolation)
	bpy.utils.unregister_class(LinearInterpolationInspector)
	bpy.utils.unregister_class(Interpolate)
	bpy.utils.unregister_class(InterpolateResetMesh)
	bpy.utils.unregister_class(InterpolateAddMesh)
	bpy.utils.unregister_class(InterpolateWithBmesh)
	bpy.utils.unregister_class(SimpleMouseOperator)
	bpy.utils.unregister_class(ModalOperator)
	bpy.utils.unregister_class(IncrementBrushIndex)
	bpy.utils.unregister_class(DecrementBrushIndex)
	bpy.utils.unregister_class(InterpolationBrushOperator)

if __name__ == "__main__":
    register()
