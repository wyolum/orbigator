// Render 10x10mm aluminum extrusion in its assembly position
// Export with: openscad -o stls_in_situ/1010_extrusion.stl render_1010_extrusion.scad

// 1010 aluminum extrusion profile
// Replace this module with a real profile import if desired
module al_1010_extrusion(length=300) {
    // Simple 10x10 cube for now
    // Could be replaced with: import("1010_profile.stl");
    cube([10, 10, length], center=false);
}

// Position: top of extrusion at (0, 0, -30)
// Extrusion is 300mm long, extending downward
translate([-5, -5, -30 - 300])  // center on X/Y, top at z=-30
    al_1010_extrusion(300);
