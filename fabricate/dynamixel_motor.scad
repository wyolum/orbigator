/*
 * Dynamixel Motor Model
 * Parametric OpenSCAD model for Dynamixel servo motors
 * Default dimensions based on XL330-M288-T
 * 
 * Author: Generated for Orbigator project
 * Date: 2025-12-13
 */

// Main parameters for XL330-M288-T
// All dimensions in mm
motor_width = 20;           // Width of motor body
motor_depth = 34;           // Depth of motor body
motor_height = 23;        // Height of motor body (excluding horn)
shaft_offset_from_top = 9.5; // Distance from top of motor to shaft center

// Horn parameters
horn_diameter = 16;       // Diameter of output horn
horn_height = 2.8;          // Height of horn above body
horn_screw_diameter = 2;    // Center screw hole
horn_mount_holes = 4;       // Number of mounting holes in horn
horn_mount_radius = 6;      // Radius of mounting holes from center
horn_mount_hole_dia = 2;    // Diameter of mounting holes
horn_mount_hole_xtra = 0.4;  // extra diameter for mounting screws
horn_mount_head_dia = 5;    // Diameter of mounting holes

// Side mounting bracket parameters
bracket_width = 24;         // Width of mounting bracket
bracket_height = 5;         // Height of mounting bracket
bracket_thickness = 3;      // Thickness of bracket
bracket_hole_spacing_x = 16;  // Distance between mounting holes
bracket_hole_spacing_y = 30;  // Distance between mounting holes
bracket_hole_diameter = 2; // Mounting hole diameter

// Cable parameters
cable_width = 4;            // Width of cable connector
cable_height = 3;           // Height of cable connector
cable_depth = 6;            // Depth of cable connector

// Drive shaft adapter parameters
adapter_base_height = 3.2;   // Height of base that sits on horn
taper_height = 3;            // Height of tapered transition
shaft_diameter = 5;          // Diameter of D-shaft
shaft_height = 18;           // Total height of shaft (7 + 11)
d_flat_width = 0.5;          // Width of flat on D-shaft
// Safe screw depth: goes through adapter base + into horn, but NOT through horn to motor body
// Leave 0.5mm safety margin to prevent bottoming out on motor
screw_depth = adapter_base_height + horn_height - 0.5;

// Rendering quality
$fn = 50;

// Main module
module dynamixel_xl330(show_horn=true, show_bracket=true, show_cable=true) {
  translate([0, -(motor_depth/2-shaft_offset_from_top), -motor_height-horn_height+horn_height])
    {
      color("DarkSlateGray") {
        // Main motor body
        difference() {
	  // Main rectangular body
	  translate([0, 0, motor_height/2])
	    cube([motor_width, motor_depth, motor_height], center=true);
            
	  // Mounting bracket cutouts (if brackets are shown separately)
	  if (!show_bracket) {
	    // Top bracket cutout
	    translate([0, 0, motor_height - bracket_thickness/2])
	      cube([motor_width + 0.1, bracket_width + 0.1, bracket_thickness + 0.1], center=true);
	  }
            
	  // Mounting holes through the body (4 holes at corners)
	  // Based on technical drawing - holes are on 18mm spacing
	  for (x = [-1, 1]) {
	    for (y = [-1, 1]) {
	      translate([x * bracket_hole_spacing_x / 2, y * bracket_hole_spacing_y / 2, motor_height/2])
		cylinder(h=motor_height*2, d=bracket_hole_diameter, center=true);
	    }
	  }
        }
      }
    
      // Output horn (positioned at shaft_z)
      if (show_horn) {
        color("White", 0.9) {
	  translate([0, motor_depth/2-shaft_offset_from_top, motor_height]) {
	    difference() {
	      // Horn cylinder
	      cylinder(h=horn_height, d=horn_diameter);
                    
	      // Center screw hole
	      translate([0, 0, -0.1])
		cylinder(h=horn_height + 0.2, d=horn_screw_diameter);
                    
	      // Mounting holes around horn
	      for (i = [0:horn_mount_holes-1]) {
		rotate([0, 0, i * 360/horn_mount_holes])
		  translate([horn_mount_radius, 0, -0.1])
		  cylinder(h=horn_height + 100, d=horn_mount_hole_dia,center=true);
	      }
	    }
                
	    // Horn spline (simplified as cross pattern)
	    for (i = [0:3]) {
	      rotate([0, 0, i * 90])
		translate([0, 0, horn_height/2])
		cube([horn_diameter * 0.6, 1.5, horn_height], center=true);
	    }
	  }
        }
      }
    }
}
module dynamixel_mounting_screws(){
  translate([0, -(motor_depth/2-shaft_offset_from_top), -motor_height-horn_height+horn_height])
  for (x = [-1, 1]) {
    for (y = [-1, 1]) {
      translate([x * bracket_hole_spacing_x / 2, y * bracket_hole_spacing_y / 2, motor_height/2])
	cylinder(h=motor_height*2, d=bracket_hole_diameter, center=true);
      translate([x * bracket_hole_spacing_x / 2, y * bracket_hole_spacing_y / 2, motor_height*2+1])
	cylinder(h=motor_height*2, d=bracket_hole_diameter*3, center=true);
    }
  }
}

// Mounting bracket module (can be used separately for assemblies)
module dynamixel_bracket(thickness=3) {
    difference() {
        cube([motor_width, bracket_width, thickness], center=true);
        
        // Mounting holes
        for (y = [-1, 1]) {
            translate([0, y * bracket_hole_spacing/2, 0])
                cylinder(h=thickness + 0.2, d=bracket_hole_diameter, center=true);
        }
    }
}

// Horn module (can be used separately)
module dynamixel_horn() {
    difference() {
        // Horn cylinder
        cylinder(h=horn_height, d=horn_diameter);
        
        // Center screw hole
        translate([0, 0, -0.1])
            cylinder(h=horn_height + 0.2, d=horn_screw_diameter);
        
        // Mounting holes around horn
        for (i = [0:horn_mount_holes-1]) {
            rotate([0, 0, i * 360/horn_mount_holes])
                translate([horn_mount_radius, 0, -0.1])
                    cylinder(h=horn_height + 0.2, d=horn_mount_hole_dia);
        }
    }
    
    // Horn spline
    for (i = [0:3]) {
        rotate([0, 0, i * 90])
            translate([0, 0, horn_height/2])
                cube([horn_diameter * 0.6, 1.5, horn_height], center=true);
    }
}

// Drive shaft adapter module
// Mounts to DYNAMIXEL horn and provides D-shaft output
module dynamixel_drive_shaft(){
  translate([0, 0, horn_height]){
    difference(){
      union(){
        // Base adapter that sits on horn
	cylinder(d=horn_diameter, h=adapter_base_height);
        // Tapered transition from horn to shaft
	translate([0, 0, adapter_base_height])
          cylinder(d2=shaft_diameter, d1=horn_diameter, h=taper_height);
      }
      // Mounting holes for self-tapping screws
      for (i = [0:horn_mount_holes-1]) {
        // Through holes for screw shafts
	rotate([0, 0, i * 360/horn_mount_holes])
	  translate([horn_mount_radius, 0, -1])
	  cylinder(h=screw_depth, d=horn_mount_hole_dia+horn_mount_hole_xtra);
        // Countersink for screw heads
	rotate([0, 0, i * 360/horn_mount_holes])
	  translate([horn_mount_radius, 0, adapter_base_height])
	  cylinder(h=screw_depth, d=horn_mount_head_dia);
      }
    }
    // D-shaft output (rotated 180° for orientation)
    rotate([0, 0, 180])
      difference(){
        // Main shaft cylinder
        cylinder(d=shaft_diameter, h=shaft_height);
        // Cut flat to create D-profile
        translate([-shaft_diameter, shaft_diameter/2 - d_flat_width, 0])
          cube([shaft_diameter*2, shaft_diameter, shaft_height + screw_depth]);
    }
  }
}
translate([0, 0, 0])color("grey")dynamixel_drive_shaft();

// Example usage: Single motor
//dynamixel_xl330(show_horn=true, show_bracket=true, show_cable=true);
//dynamixel_mounting_screws();
// Example: Daisy chain configuration (uncomment to see)
/*
for (i = [0:1]) {
    translate([0, i * (motor_depth + 5), 0])
        dynamixel_xl330();
}
*/

// Example: Motor without horn (uncomment to see)
/*
translate([40, 0, 0])
    dynamixel_xl330(show_horn=false);
*/
