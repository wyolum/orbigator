/*
 * AoV Arm for Orbigator
 * Mounts to DYNAMIXEL motor horn and provides pointer arm for globe
 * 
 * Author: Orbigator project
 * Date: 2025-12-18
 */

// Import motor constants from dynamixel_motor.scad
use <dynamixel_motor.scad>
use <sled.scad>
// Unit conversions
inch = 25.4;

// Globe parameters
globe_d = 299; // was 13 * inch;
globe_r = globe_d/2;
globe_thickness = 2;
globe_ir = globe_r - globe_thickness;
globe_id = 2 * globe_ir;

if(false){
  translate([-(globe_ir+.7), 0, 0])magnets();
  difference(){
    sphere(globe_r);
    sphere(globe_ir, $fn=50);
    translate([0,0, globe_r])cube(globe_d+1, center=true);
  }
 }
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
      translate([0, 0, 1])
        translate([-offset_distance, 0, 0])
          cylinder(d=penny_d, h=height*2);
      translate([0, 0, 1])
        translate([-offset_distance, 0, -2])
          cylinder(d=penny_d-3, h=height*2);
    }
}

module shell(od, id, h){
  difference(){
    cylinder(d=od, h=h,center=true, $fn=50);
    cylinder(d=id, h=h+2,center=true, $fn=50);
  }
}
//translate([0,0,2.5])shell(globe_d, globe_id, 5);
module aov_arm(){
  rotate([0, 0, 180]) {
    difference() {
      union() {
        // Base mounting flange (mounts to motor horn)
        cylinder(d=arm_base_diameter, h=arm_height + 0.25); // Extra height for screw clearance
        
        // Arm extending to globe edge
        rotate([0,0,20.75])
	  hull() {
          cylinder(d=arm_base_diameter+2, h=arm_height);
          translate([globe_ir - magnet_support_offset-12, -2, 0])
	    scale(1)cube([0.1, 3.6, arm_height]);
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
      // These align with horn_mount_holes from dynamixel_motor.scad
      for(i = [1:4]) {
        rotate([0, 0, 90 * i])
          translate([6, 0, -1]){  // 6mm = horn_mount_radius
            cylinder(d=2.4, h=30, $fn=30);  // Slightly larger than horn_mount_hole_dia (2mm)
	    translate([0,0,3.5])cylinder(d1=2.4, d2=3, h=1, $fn=30);  // Slightly larger than horn_mount_hole_dia (2mm)
	}
	cylinder(d=5, h=10, center=true, $fn=30);
      }
      translate([0,0,3.25])cylinder(d=arm_base_diameter, h=arm_height); // Extra height for screw clearance

    }
    
  }
}

module semicircle(r, h){
  difference(){
    cylinder(r=r, h=h);
    translate([r, 0, 0])cube(2*r, center=true);
  }
}


// Render the arm
//projection(cut=false){}
  rotate([0,0,0])color("yellow")aov_arm();
//color([0,0,1,.1])sphere(globe_ir);
//translate([-(globe_r+.5), 0,0])rotate([0,0,5])magnets();
  //rotate([0,0,180])cube([globe_ir, 10, 10]);

module tip(){
  translate([.5, 0, 0]){
    rotate([0,0,7])translate([-globe_r+7, -2, 0])semicircle(7., 1);
    translate([-globe_r+5.4, 21, 0])rotate([0,0,3.7])semicircle(7., 1);
  }
  
  difference(){
    translate([-142.5, -92, 0])linear_extrude(height=5)import("images/flex_aov_arm_2.svg");
    translate([-60,1,0])rotate([0,0,5])translate([0,0,2.5])rotate([0, -90, 0])
      cylinder(d=3, h=globe_d, $fn=30);
    translate([-60,14.5,0])rotate([0,0,5])translate([0,0,2.5])rotate([0, -90, 0])
      cylinder(d=3, h=globe_d, $fn=30);
    //translate([-(globe_r+2), 0,2])rotate([0,0,5])magnets();
  }
}
translate([1, 0, 0])tip();

//shell(globe_d, globe_id, 5);
