import os
import FreeCAD
import Mesh
import Part
import MeshPart
import sys

def convert(stl_path, step_path):
    print(f"Converting: {stl_path}")
    print(f"To: {step_path}")
    
    try:
        doc = FreeCAD.newDocument("Conversion")
        
        # Read STL
        mesh = Mesh.read(stl_path)
        mesh_obj = doc.addObject("Mesh::Feature", "Mesh")
        mesh_obj.Mesh = mesh
        
        # Convert to Shape
        shape = Part.Shape()
        shape.makeShapeFromMesh(mesh_obj.Mesh.Topology, 0.1)
        
        # Convert to Solid
        solid = Part.makeSolid(shape)
        
        # Export STEP
        solid.exportStep(step_path)
        
        FreeCAD.closeDocument("Conversion")
        print("Success!")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    stl_in = "/home/justin/code/orbigator/fabricate/stls/base_with_1010_display.stl"
    step_out = "/home/justin/code/orbigator/fabricate/step_files/base_with_1010_display.step"
    
    os.makedirs(os.path.dirname(step_out), exist_ok=True)
    convert(stl_in, step_out)
