# Copyright (c) 2022 NVIDIA CORPORATION.  All rights reserved.
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.



import omni.ext
import omni.ui as ui
import omni.usd
from .RhinoComputeFunctions import RhinoFunctions, GrasshopperFunctions
from .RhinoComputUtil import SaveSelectedAs3dm

# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class MyExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def __init__(self): 
        self.computeUrl="http://localhost:6500/"
        self.progressbarprog = 0
        self.progbarwindow = None
        self.excludeLastGroupAsLayer = False

  

    def on_startup(self, ext_id):
        #print("[omni.RhinoCompute] MyExtension startup")

        self._window = ui.Window("Rhino Compute Functions", width=300, height=400)
        with self._window.frame:
            with ui.VStack():
                with ui.CollapsableFrame("Util Functions", height = 0):
                    with ui.VStack():
                        ui.Button("save sel as 3dm", clicked_fn=lambda: SaveSelectedAs3dm(self,"S:/test.3dm"), height=40)
                        ui.Button("save all as 3dm", clicked_fn=lambda: RhinoFunctions.SaveAllAs3DM_UI(self), height=40)
                with ui.CollapsableFrame("Mesh Functions", height = 0):
                    with ui.VStack():
                        ui.Button("Volume", clicked_fn=lambda: RhinoFunctions.MeshVolume(self), height=40)
                        ui.Button("Mesh Bool Union", clicked_fn=lambda: RhinoFunctions.MeshBoolUnion(self), height=40)
                        ui.Button("Quad Remesh", clicked_fn=lambda: RhinoFunctions.MeshQuadRemesh(self), height=40)
                        ui.Button("Mesh Offset", clicked_fn=lambda: RhinoFunctions.MeshOffset(self), height=40)
                with ui.CollapsableFrame("Grasshopper Functions", height = 0):
                    with ui.VStack():
                        ui.Button("Random Diamonds Script", clicked_fn=lambda: GrasshopperFunctions.randomDiamonds_UI(self), height=40)
                
    def on_shutdown(self):
        print("[omni.RhinoCompute] MyExtension shutdown")
