import os
import FreeCAD
print("FreeCAD version:", FreeCAD.Version())
print("Current dir:", os.getcwd())
print("Files in /home/justin/code/orbigator/fabricate/stls/:")
try:
    print(os.listdir("/home/justin/code/orbigator/fabricate/stls/"))
except Exception as e:
    print(e)
