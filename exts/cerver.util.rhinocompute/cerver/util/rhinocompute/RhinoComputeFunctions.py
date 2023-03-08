# Copyright (c) 2022 NVIDIA CORPORATION.  All rights reserved.
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

import string

import omni.ext
import omni.ui as ui
from pxr import Usd, UsdGeom
import omni.usd
import carb.events
import omni.kit.app
import os

import json
import time

omni.kit.pipapi.install("rhino3dm")
from  rhino3dm import *

omni.kit.pipapi.install("compute-rhino3d")
import compute_rhino3d.Util
import compute_rhino3d.Mesh
import compute_rhino3d.Grasshopper as gh
from .RhinoComputUtil import *

omni.kit.pipapi.install("plotly==5.4.0")
import plotly.graph_objects as go



class RhinoFunctions:

    def ComputeServerUrl(self):
        return  self.computeUrl

    def MeshVolume(self):
        #add the compute server location
        compute_rhino3d.Util.url = self.computeUrl

        #convert selected items to rhino mesh
        meshes = convertSelectedUsdMeshToRhino()
        
        
        vols = []
        names = []
        rhinoMeshes = []

        #for each mesh compute the volume and then add the volume and name to a list
        for m in meshes:
            rhinoMeshes.append(m["Mesh"])
            vol = compute_rhino3d.Mesh.Volume(m["Mesh"])
            vols.append(vol)
            names.append(m["Name"])
        
        #use plotly to plot the volumes as a pie chart
        fig = go.Figure(
            data=[go.Pie(values=vols, labels=names)],
            layout_title_text="the Volumes"
        )
        fig.show()
    
    def MeshBoolUnion(self) -> None:
        #add the compute server location
        compute_rhino3d.Util.url = self.computeUrl
        
        #convert selected items to rhino mesh
        meshes = convertSelectedUsdMeshToRhino()

        #for each mesh compute the bool union
        rhinoMeshes = []
        for m in meshes:
            rhinoMeshes.append(m["Mesh"])
        rhinoMeshes = compute_rhino3d.Mesh.CreateBooleanUnion(rhinoMeshes)
        
        #add to the stage after converting back from rhino to USD mesh
        #ToDo: add UI to define prim path and names
        ct=0
        for rm in rhinoMeshes:
            RhinoMeshToUsdMesh("/World/rhinoComputed/",f"BoolUnion_{ct}",rm)
    
    def MeshQuadRemesh(self)-> None:
        compute_rhino3d.Util.url = self.computeUrl
        meshes = convertSelectedUsdMeshToRhino()

        #setup all the params for quad remesh
        #ToDo: make this a UI for user
        parameters = {
            'AdaptiveQuadCount': True, 
            'AdaptiveSize': 50.0, 
            'DetectHardEdges': True, 
            'GuideCurveInfluence': 0, 
            'PreserveMeshArrayEdgesMode': 0, 
            'TargetQuadCount': 2000
        }
        names = []
        rhinoMeshes = []
   
        for m in meshes:
            weldVerts =  compute_rhino3d.Mesh.Weld(m["Mesh"],0.5)
            qrm =compute_rhino3d.Mesh.QuadRemesh(weldVerts,parameters)
            name = m["Name"]
            if qrm is not None:
                rhinoMeshes.append(qrm)
                names.append(name)
                RhinoMeshToUsdMesh("/World/rhinoComputed/",name+"_QuadRemesh",qrm)
            else:
                warning(f"QuadRemesh Failed on {name}")
        
    def MeshWeld(self, tol)-> None:
        compute_rhino3d.Util.url = self.computeUrl
        meshes = convertSelectedUsdMeshToRhino()

        names = []
        rhinoMeshes = []
   
        for m in meshes:
            weldVerts =  compute_rhino3d.Mesh.Weld(m["Mesh"],tol)
            name = m["Name"]
            if weldVerts is not None:
                rhinoMeshes.append(weldVerts)
                names.append(name)
                RhinoMeshToUsdMesh("/World/rhinoComputed/",name+"_Weld",weldVerts)
            else:
                warning(f"Weld Failed on {name}")
 
    def MeshOffset(self)-> None:
        compute_rhino3d.Util.url = self.computeUrl
        meshes = convertSelectedUsdMeshToRhino()

        names = []
        rhinoMeshes = []
        for m in meshes:
            macf = compute_rhino3d.Mesh.Offset1(m["Mesh"],1,True)
            rhinoMeshes.append(macf)
            name = m["Name"]
            names.append(name)
            RhinoMeshToUsdMesh("/World/rhinoComputed/",name+"_offset",macf)

   

    def SaveAllAs3DM_UI(self):
        window_flags = ui.WINDOW_FLAGS_NO_SCROLLBAR
        #window_flags |= ui.WINDOW_FLAGS_NO_TITLE_BAR
        self.export3dmwindow = ui.Window("Export Stage As 3DM", width=300, height=130, flags=window_flags)
        with self.export3dmwindow.frame:   
            with ui.VStack():
                with ui.HStack():
                    ui.Label("Path", width=50, height = 25)
                    path = ui.StringField( height = 25, tooltip = "Set the location and name of the file i.e c:/temp/myRhinofile.3dm")
                with ui.HStack( height = 35):
                    def exLastGrpAsLayCb_changed(self, val):
                        self.excludeLastGroupAsLayer = val
                        print(val)
                    
                    exLastGrpAsLayCb = ui.CheckBox(width = 30)
                    exLastGrpAsLayCb.model.add_value_changed_fn(lambda cb: exLastGrpAsLayCb_changed(self,cb.get_value_as_bool() ) )
                    ui.Label("Exlude last group as layer", width=50, height = 15)
                    
                def exportbt():
                    SaveAllas3DM(self,path.model.get_value_as_string())
                ui.Line()
                ui.Button("Export", clicked_fn=lambda: exportbt(), height=25)



class GrasshopperFunctions:

    def randomDiamonds(self,uCt,vCt,rrA,rrB):
        compute_rhino3d.Util.url = self.computeUrl
        
        ghFile = os.path.dirname(os.path.dirname(__file__)) + "/rhinocompute/gh/randomDiamonds.ghx"
        selectedMeshes = convertSelectedUsdMeshToRhino()
        inputMesh = selectedMeshes[0]["Mesh"]
        

        # create list of input trees
        ghMesh = json.dumps(inputMesh.Encode())
        mesh_tree = gh.DataTree("baseMesh")
        mesh_tree.Append([0], [ghMesh])

        srfU_tree = gh.DataTree("srfU")
        srfU_tree.Append([0], [uCt])

        srfV_tree = gh.DataTree("srfV")
        srfV_tree.Append([0], [vCt])

        rrA_tree = gh.DataTree("RR_A")
        rrA_tree.Append([0], [rrA])

        rrB_tree = gh.DataTree("RR_B")
        rrB_tree.Append([0], [rrB])


        inputs = [mesh_tree, srfU_tree, srfV_tree, rrA_tree, rrB_tree]

        results = gh.EvaluateDefinition(ghFile, inputs)
        
        
        # decode results
        
        data = results['values'][0]['InnerTree']['{0}']
        outMeshes = [rhino3dm.CommonObject.Decode(json.loads(item['data'])) for item in data]
  
        ct = 0
        for m in outMeshes:
            RhinoMeshToUsdMesh("/World",f"/randomDiamonds/randomDiamonds_{ct}",m)
            ct+=1

    def randomDiamonds_UI(self):
        def run(uCt,vCt,rrA,rrB):
            GrasshopperFunctions.randomDiamonds(self,uCt, vCt, rrA,rrB)
        
        #window_flags = ui.WINDOW_FLAGS_NO_RESIZE
        sliderStyle = {"border_radius":15, "background_color": 0xFFDDDDDD, "secondary_color":0xFFAAAAAA, "color":0xFF111111, "margin":3}

        window_flags = ui.WINDOW_FLAGS_NO_SCROLLBAR
        self.theWindow = ui.Window("Random Diamonds", width=300, height=200, flags=window_flags)
        with self.theWindow.frame:
            with ui.VStack():
                with ui.HStack():
                    ui.Label("U Ct", width=40)
                    srfU = ui.IntSlider(height= 20, min=1, max=50, style= sliderStyle )
                with ui.HStack():
                    ui.Label("V Ct", width=40)
                    srfV = ui.IntSlider(height= 20, min=1, max=50, style= sliderStyle )
                with ui.HStack():
                    ui.Label("min D", width=40)
                    rrA = ui.FloatSlider(height= 20, min=0.1, max=150, style= sliderStyle )
                with ui.HStack():
                    ui.Label("max D", width=40)
                    rrB = ui.FloatSlider(height= 20, min=0.1, max=150, style= sliderStyle )

                srfU.model.set_value(4)
                srfV.model.set_value(4)
                rrA.model.set_value(4)
                rrB.model.set_value(75)

                srfU.model.add_value_changed_fn(lambda m:run(srfU.model.get_value_as_int(),srfV.model.get_value_as_int(),rrA.model.get_value_as_float(),rrB.model.get_value_as_float()))
                srfV.model.add_value_changed_fn(lambda m:run(srfU.model.get_value_as_int(),srfV.model.get_value_as_int(),rrA.model.get_value_as_float(),rrB.model.get_value_as_float()))
                rrA.model.add_value_changed_fn(lambda m:run(srfU.model.get_value_as_int(),srfV.model.get_value_as_int(),rrA.model.get_value_as_float(),rrB.model.get_value_as_float()))
                rrB.model.add_value_changed_fn(lambda m:run(srfU.model.get_value_as_int(),srfV.model.get_value_as_int(),rrA.model.get_value_as_float(),rrB.model.get_value_as_float()))

                ui.Line(height=10)
                ui.Button("Run >>", clicked_fn=lambda: GrasshopperFunctions.randomDiamonds(self, 
                    srfU.model.get_value_as_int(),
                    srfV.model.get_value_as_int(),
                    rrA.model.get_value_as_float(),
                    rrB.model.get_value_as_float(),
                    ), height=30)