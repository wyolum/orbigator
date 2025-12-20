/*
 * AoV Arm for Orbigator
 * Mounts to DYNAMIXEL motor horn and provides pointer arm for globe
 * 
 * Author: Orbigator project
 * Date: 2025-12-18
 */

// Import motor constants from dynamixel_motor.scad
use <dynamixel_motor.scad>

// Unit conversions
inch = 25.4;

// Globe parameters
globe_d = 13 * inch;
globe_r = globe_d/2;
globe_thickness = 2;
globe_ir = globe_r - globe_thickness;

// Arm parameters
arm_height = 5;
arm_base_diameter = 20;  // Slightly larger than horn_diameter (16mm) for clearance

// Magnet/weight compartment parameters
magnet_support_offset = 8;  // Offset from globe_ir
penny_radius = 70;
penny_angle = 9;  // Angle for dual penny compartments

// Penny dimensions (for counterweight)
um3_tol = 0.2;
penny_d = 0.75 * inch + um3_tol;
penny_t = 0.06 * inch;
penny_compartment_height = 15;

// Motor horn mounting parameters (from dynamixel_motor.scad)
// horn_diameter = 16
// horn_mount_holes = 4
// horn_mount_radius = 6
// horn_mount_hole_dia = 2

module penny_compartment(offset_distance, angle=0, height) {
  rotate([0, 0, 180 + angle])
    difference() {
      hull() {
        translate([-offset_distance, 0, 0])
          cylinder(d=penny_d + 4, h=height);
      }
      // Penny cavity
      translate([0, 0, -2])
        translate([-offset_distance, 0, 0])
          cylinder(d=penny_d, h=height);
      // Inner clearance
      translate([0, 0, -2])
        translate([-offset_distance, 0, 0])
          cylinder(d=penny_d * 0.9, h=height * 2);
    }
}

module aov_arm() {
  rotate([0, 0, 180]) {
    difference() {
      union() {
        // Base mounting flange (mounts to motor horn)
        cylinder(d=arm_base_diameter, h=arm_height + 0.25); // Extra height for screw clearance
        
        // Arm extending to globe edge
        hull() {
          cylinder(d=arm_base_diameter, h=arm_height);
          translate([globe_ir - 1, -2, 0])
            cube([0.1, 4, arm_height]);
        }
        
        // Arm extending to counterweight
        hull() {
          cylinder(d=arm_base_diameter, h=arm_height);
          translate([-penny_radius + 5, -2, 0])
            cube([0.1, 4, arm_height]);
        }
        
        // Counterweight compartments
        rotate([0, 0, 180])
          penny_compartment(penny_radius, penny_angle, penny_compartment_height);
        rotate([0, 0, 180])
          penny_compartment(penny_radius, -penny_angle, penny_compartment_height);
      }
      
      // Mounting holes for motor horn (4 holes at 45° intervals)
      // These align with horn_mount_holes from dynamixel_motor.scad
      for(i = [1:4]) {
        rotate([0, 0, 45 + 90 * i])
          translate([6, 0, -1])  // 6mm = horn_mount_radius
            cylinder(d=2, h=30, $fn=30);  // Slightly larger than horn_mount_hole_dia (2mm)
      }
    }
    
    // Globe engagement feature (partial ring that grips globe)
    intersection() {
      difference() {
        // Outer ring
        cylinder(r=globe_ir, h=7, $fn=50);
        
        // Inner clearance
        translate([0, 0, -1])
          cylinder(r=globe_ir - 2, h=arm_height + 12, $fn=50);
        
        // Horizontal clearance slot
        rotate([90, 0, 0])
          translate([0, 8, 0])
            cylinder(d=5, h=30, $fn=30);
        
        // Angled mounting holes for globe attachment
        rotate([0, 0, 180 + 2.6])
          translate([-200, 0, 3.4])
            rotate([0, 90, 0])
              cylinder(d=3.5, h=100, $fn=30);
        
        rotate([0, 0, 180 - 2.6])
          translate([-200, 0, 3.4])
            rotate([0, 90, 0])
              cylinder(d=3.5, h=100, $fn=30);
      }
      
      // Trim to half-ring
      translate([100, 0, 0])
        cube([200, 25, 100], center=true);
    }
  }
}

// Render the arm
color("yellow")aov_arm();
