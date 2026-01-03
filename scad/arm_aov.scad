/*
 * AoV Arm for Orbigator
 */

include <common.scad>
include <motor_dynamixel.scad>

// Arm parameters
arm_height = 5;
arm_base_diameter = 20;  // Slightly larger than horn_diameter (16mm) for clearance

// Magnet/weight compartment parameters
magnet_support_offset = 9;  // Offset from globe_ir
penny_radius = 70;
penny_angle = 9;  // Angle for dual penny compartments

// Penny dimensions (for counterweight)
um3_tol = 0.2;
penny_d = 0.75 * inch + um3_tol;
penny_t = 0.06 * inch;
penny_compartment_height = 15;

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
          cylinder(d=penny_d, h=height*2);
      // Inner clearance
      translate([0, 0, -2])
        translate([-offset_distance, 0, 0])
          cylinder(d=penny_d * 0.9, h=height * 2);
    }
}

// magnets() is defined in sled.scad

module aov_arm() {
  globe_ir = globe_r - 2; // Default thickness
  rotate([0, 0, 180]) {
    difference() {
      union() {
        // Base mounting flange (mounts to motor horn)
        cylinder(d=arm_base_diameter, h=arm_height + 0.25); 
        
        // Arm extending to globe edge
        hull() {
          cylinder(d=arm_base_diameter+2, h=arm_height);
          translate([globe_ir - 1 - magnet_support_offset, -2, 0])
            cube([0.1, 4, arm_height]);
        }
        
        // Arm extending to counterweight
        hull() {
          cylinder(d=arm_base_diameter+2, h=arm_height);
          translate([-penny_radius + 5, -2, 0])
            cube([0.1, 4, arm_height]);
        }
        
        // Counterweight compartments
        rotate([0, 0, 180])
          penny_compartment(penny_radius, penny_angle, penny_compartment_height);
        rotate([0, 0, 180])
          penny_compartment(penny_radius, -penny_angle, penny_compartment_height);
      }
      
      // Mounting holes for motor horn (4 holes at 90° intervals)
      // These align with horn_mount_holes from motor_dynamixel.scad
      for(i = [1:horn_mount_holes]) {
        rotate([0, 0, 360/horn_mount_holes * i])
          translate([horn_mount_radius, 0, -1]){  
            cylinder(d=horn_mount_hole_dia + 0.4, h=30, $fn=30);  
	    translate([0,0,3.5])cylinder(d1=horn_mount_hole_dia + 0.4, d2=3, h=1, $fn=30);  
	}
      }
      translate([0,0,3.25])cylinder(d=arm_base_diameter, h=arm_height); 

    }
    
    // Globe engagement feature
    intersection() {
      difference() {
        cylinder(r=globe_ir-magnet_support_offset, h=7, $fn=50);
        translate([0, 0, -1])
          cylinder(r=globe_ir - 2-magnet_support_offset, h=arm_height + 12, $fn=50);
        rotate([90, 0, 0])
          translate([0, 8, 0])
            cylinder(d=5, h=30, $fn=30);
        rotate([0, 0, 180 + 2.6])
          translate([-200, 0, 3.4])
            rotate([0, 90, 0])
              cylinder(d=3.5, h=100, $fn=30);
        rotate([0, 0, 180 - 2.6])
          translate([-200, 0, 3.4])
            rotate([0, 90, 0])
              cylinder(d=3.5, h=100, $fn=30);
      }
      translate([100, 0, 0])
        cube([200, 25, 100], center=true);
    }
  }
}

if ($show_demo) {
    color("yellow") aov_arm();
}
