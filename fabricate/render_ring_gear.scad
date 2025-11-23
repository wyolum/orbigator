// Render Ring (ring gear) in its assembly position
// Export with: openscad -o stls_in_situ/ring_gear.stl render_ring_gear.scad

use <full_assembly.scad>

// No transformation - Ring is at origin in assembly
Ring();
