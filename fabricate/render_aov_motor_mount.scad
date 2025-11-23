// Render aov_motor_mount in its assembly position
// Export with: openscad -o stls_in_situ/aov_motor_mount.stl render_aov_motor_mount.scad

use <stepper_motors.scad>

// Assembly parameters (from full_assembly.scad line 382)
inc = 65;

// Full transformation chain from aov_motor_assy module
translate([0, 0, -140])
  translate([0, 0, 150])
    translate([0, 0, -10])
      rotate([inc, 0, 0])
        rotate([0, 180, 0])
          aov_motor_mount();
