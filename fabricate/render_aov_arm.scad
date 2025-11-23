// Render aov_arm as positioned in assembly
// Export with: openscad -o stls/aov_arm_oriented.stl render_aov_arm.scad

include <aov_arm.scad>

// Assembly values from full_assembly.scad line 382: aov_motor_assy(65, 90)
inc = 65;
aov = 90;

// Full transformation chain from aov_motor_assy module
translate([0, 0, -140])
  translate([0, -3, 140])
    rotate([inc, 0, 0])
      rotate([0, 0, aov-180])
        aov_arm();
