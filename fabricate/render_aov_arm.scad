// Render aov_arm in its assembly position
// Export with: openscad -o stls_in_situ/aov_arm.stl render_aov_arm.scad

use <aov_arm.scad>

// Assembly parameters (from full_assembly.scad line 382)
inc = 65;
aov = 90;

// Full transformation chain from aov_motor_assy module
translate([0, 0, -140])
  translate([0, -3, 140])
    rotate([inc, 0, 0])
      rotate([0, 0, aov-180])
        aov_arm();
