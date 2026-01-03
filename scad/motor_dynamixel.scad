/*
 * Dynamixel Motor Model
 */

$show_demo = false;

// Main parameters for XL330/XC330-M288-T
motor_width = 20;           
motor_depth = 34;           
motor_height = 23;        
shaft_offset_from_top = 9.5; 

// Horn parameters (shared constants)
horn_diameter = 16;       
horn_height = 2.8;          
horn_screw_diameter = 2;    
screw_head_diameter = 3.75;
horn_mount_holes = 4;       
horn_mount_radius = 6;      
horn_mount_hole_dia = 2;    
horn_mount_hole_xtra = 0.4;  
horn_mount_head_dia = 5;    

// Side mounting bracket parameters
bracket_width = 24;         
bracket_height = 5;         
bracket_thickness = 3;      
bracket_hole_spacing_x = 16;  
bracket_hole_spacing_y = 30;  
bracket_hole_diameter = 2; 

// Drive shaft adapter parameters
adapter_base_height = 3.2;   
taper_height = 3;            
shaft_diameter = 5;          
shaft_height = 18;           
d_flat_width = 0.5;          
screw_depth = adapter_base_height + horn_height - 0.5;

module dynamixel_xl330(show_horn=true, show_bracket=true, show_cable=true) {
  translate([0, -(motor_depth/2-shaft_offset_from_top), -motor_height])
    {
      color("DarkSlateGray") {
        difference() {
	  translate([0, 0, motor_height/2])
	    cube([motor_width, motor_depth, motor_height], center=true);
            
	  if (!show_bracket) {
	    translate([0, 0, motor_height - bracket_thickness/2])
	      cube([motor_width + 0.1, bracket_width + 0.1, bracket_thickness + 0.1], center=true);
	  }
            
	  for (x = [-1, 1]) {
	    for (y = [-1, 1]) {
	      translate([x * bracket_hole_spacing_x / 2, y * bracket_hole_spacing_y / 2, motor_height/2])
		cylinder(h=motor_height*2, d=bracket_hole_diameter, center=true);
	    }
	  }
        }
      }
    
      if (show_horn) {
        color("White", 0.9) {
	  translate([0, motor_depth/2-shaft_offset_from_top, motor_height]) {
	    difference() {
	      cylinder(h=horn_height, d=horn_diameter);
	      translate([0, 0, -0.1])
		cylinder(h=horn_height + 0.2, d=horn_screw_diameter);
	      for (i = [0:horn_mount_holes-1]) {
		rotate([0, 0, i * 360/horn_mount_holes])
		  translate([horn_mount_radius, 0, -0.1])
		  cylinder(h=horn_height + 100, d=horn_mount_hole_dia,center=true);
	      }
	    }
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
  translate([0, -(motor_depth/2-shaft_offset_from_top), -motor_height])
  for (x = [-1, 1]) {
    for (y = [-1, 1]) {
      translate([x * bracket_hole_spacing_x / 2, y * bracket_hole_spacing_y / 2, motor_height/2])
	cylinder(h=motor_height*2, d=bracket_hole_diameter, center=true);
      translate([x * bracket_hole_spacing_x / 2, y * bracket_hole_spacing_y / 2, motor_height*2+1])
	cylinder(h=motor_height*2, d=screw_head_diameter, center=true);
    }
  }
}

module dynamixel_bracket(thickness=3) {
    difference() {
        cube([motor_width, bracket_width, thickness], center=true);
        for (y = [-1, 1]) {
            translate([0, y * bracket_hole_spacing_y/2, 0])
                cylinder(h=thickness + 0.2, d=bracket_hole_diameter, center=true);
        }
    }
}

module dynamixel_horn() {
    difference() {
        cylinder(h=horn_height, d=horn_diameter);
        translate([0, 0, -0.1])
            cylinder(h=horn_height + 0.2, d=horn_screw_diameter);
        for (i = [0:horn_mount_holes-1]) {
            rotate([0, 0, i * 360/horn_mount_holes])
                translate([horn_mount_radius, 0, -0.1])
                    cylinder(h=horn_height + 0.2, d=horn_mount_hole_dia);
        }
    }
    for (i = [0:3]) {
        rotate([0, 0, i * 90])
            translate([0, 0, horn_height/2])
                cube([horn_diameter * 0.6, 1.5, horn_height], center=true);
    }
}

module dynamixel_drive_shaft(){
  translate([0, 0, motor_height + horn_height]){
    difference(){
      union(){
	cylinder(d=horn_diameter, h=adapter_base_height);
	translate([0, 0, adapter_base_height])
          cylinder(d2=shaft_diameter, d1=horn_diameter, h=taper_height);
      }
      for (i = [0:horn_mount_holes-1]) {
	rotate([0, 0, i * 360/horn_mount_holes])
	  translate([horn_mount_radius, 0, -1])
	  cylinder(h=screw_depth, d=horn_mount_hole_dia+horn_mount_hole_xtra);
	rotate([0, 0, i * 360/horn_mount_holes])
	  translate([horn_mount_radius, 0, adapter_base_height])
	  cylinder(h=screw_depth, d=horn_mount_head_dia);
      }
    }
    rotate([0, 0, 180])
      difference(){
        cylinder(d=shaft_diameter, h=shaft_height);
        translate([-shaft_diameter, shaft_diameter/2 - d_flat_width, 0])
          cube([shaft_diameter*2, shaft_diameter, shaft_height + screw_depth]);
    }
  }
}

// Gated demo
if ($show_demo) {
    color("DarkSlateGray") dynamixel_xl330();
    color("grey") dynamixel_drive_shaft();
}
