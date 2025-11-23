// Render base_with_1010_hole in its assembly position
// Export with: openscad -o stls_in_situ/base_with_1010_hole.stl render_base_with_1010_hole.scad

use <full_assembly.scad>

// No transformation - base is at origin in assembly
base_with_1010_hole();
