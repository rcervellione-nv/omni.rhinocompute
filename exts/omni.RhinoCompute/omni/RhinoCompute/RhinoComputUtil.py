# Copyright (c) 2022 NVIDIA CORPORATION.  All rights reserved.
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import compute_rhino3d.Util
import compute_rhino3d.Mesh
import compute_rhino3d.Grasshopper as gh
import rhino3dm
import json
import omni.ext
import omni.ui as ui
from pxr import Usd, UsdGeom, Gf
import omni.usd



def convertSelectedUsdMeshToRhino():
    context = omni.usd.get_context()
    stage = omni.usd.get_context().get_stage()
    prims = [stage.GetPrimAtPath(m) for m in context.get_selection().get_selected_prim_paths() ]

    #filter out prims that are not mesh
    selected_prims = [
            prim for prim 
            in prims
            if UsdGeom.Mesh(prim)]
    
    #setup var to hold the mesh, its name in the dict
    sDict = []

    #add the converted prims to the dict
    for m in selected_prims:
        sDict.append({"Name": m.GetName(), "Mesh":UsdMeshToRhinoMesh(m)})
    
    return  sDict

def UsdMeshToRhinoMesh(usdMesh):
    #array for the mesh items
    vertices = []
    faces = []

    #get the USD points
    points  = UsdGeom.Mesh(usdMesh).GetPointsAttr().Get()
    
    #setup the items needed to deal with world and local transforms
    xform_cache = UsdGeom.XformCache()
    mtrx_world = xform_cache.GetLocalToWorldTransform(usdMesh)

    #create the rhino mesh
    mesh = rhino3dm.Mesh()

    #convert the USD points to rhino points
    for p in points:
        world_p = mtrx_world.Transform(p)
        mesh.Vertices.Add(world_p[0],world_p[1],world_p[2])  
    
    #faces we can extend directly into the aray becaue they are just ints
    faces.extend( UsdGeom.Mesh(usdMesh).GetFaceVertexIndicesAttr().Get())
    faceCount = UsdGeom.Mesh(usdMesh).GetFaceVertexCountsAttr().Get()

    ct = 0
    #add the face verts, USD uses a flat list of ints so we need to deal with
    #3 or 4 sided faces. USD supports ngons but that is not accounted for
    #ToDo: Deal with ngons
    for i in range(0,len(faceCount)):
        fc=faceCount[i] 
        if fc is 3:
            mesh.Faces.AddFace(faces[ct], faces[ct+1], faces[ct+2])
        if fc  is 4:
            mesh.Faces.AddFace(faces[ct], faces[ct+1], faces[ct+2], faces[ct+3])
        ct+=fc
    
    #compute normals, i dont use the USD normals here but you could
    mesh.Normals.ComputeNormals()
    mesh.Compact()

    return mesh

def save_stage():
    stage = omni.usd.get_context().get_stage()
    stage.GetRootLayer().Save()
    omni.client.usd_live_process()
    
def RhinoMeshToUsdMesh( rootUrl, meshName, rhinoMesh: rhino3dm.Mesh , primPath=None):
    #get the stage
    stage = omni.usd.get_context().get_stage()

    
	# Create the geometry inside of "Root"
    meshPrimPath = rootUrl + meshName
    mesh = UsdGeom.Mesh.Define(stage, meshPrimPath)
    
	# Add all of the vertices
    points = []

    for i in range(0,len(rhinoMesh.Vertices)):
        v = rhinoMesh.Vertices[i]
        points.append(Gf.Vec3f(v.X, v.Y, v.Z))
    mesh.CreatePointsAttr(points)


	# Calculate indices for each triangle
    faceIndices = []
    faceVertexCounts = []
    fcount=3
    
    for i in range(0, rhinoMesh.Faces.Count):
        curf = rhinoMesh.Faces[i]
        faceIndices.append(curf[0])
        faceIndices.append(curf[1])
        faceIndices.append(curf[2])
        if curf[2] != curf[3]:
            faceIndices.append(curf[3])
            fcount=4
        #print(fcount)
        faceVertexCounts.append(fcount)

    mesh.CreateFaceVertexIndicesAttr(faceIndices)
    mesh.CreateFaceVertexCountsAttr(faceVertexCounts)
    
	# Add vertex normals
    meshNormals = []
    for n in rhinoMesh.Normals:
        meshNormals.append(Gf.Vec3f(n.X,n.Y,n.Z))
    mesh.CreateNormalsAttr(meshNormals)
 
def SaveRhinoFile(rhinoMeshes, path):
    model = rhino3dm.File3dm()
    [ model.Objects.AddMesh(m) for m in rhinoMeshes]
    model.Write(path)

def SaveSelectedAs3dm(self,path):
    selectedMeshes = convertSelectedUsdMeshToRhino()
    meshobj = [d['Mesh'] for d in selectedMeshes]
    SaveRhinoFile(meshobj, path)
