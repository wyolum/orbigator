// Render aov_arm as positioned in assembly
// Adjust inc and aov values as needed, then export to STL

include <aov_arm.scad>

// Assembly orientation parameters
inc = 0;      // inclination angle
aov = 180;    // angle of view

// Apply rotations as in aov_motor_assy
rotate([inc, 0, 0])
  rotate([0, 0, aov-180])
    aov_arm();
