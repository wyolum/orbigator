include <MCAD/units.scad>
include <MCAD/materials.scad>
use <dynamixel_motor.scad>

//color("red")motor(Nema14, NemaShort, dualAxis=false)

module dynamixel_motor_mount_arc(){
  union(){
    translate([-3.0-4, 0, 0])difference(){
      union(){
	rotate([0, -90, 180])wedge(4, 50, 90);
	translate([-2,0,0])cube([4, 15,50]);
	translate([0,-12.,.75])rotate([90, 0, 0])wedge(2, 20, 90);
	translate([0, 12.,.75])rotate([90, 0, 0])wedge(2, 20, 90);
      }
      hull(){
	translate([7,0,0])rotate([0,0,-90])rotate([0,180,180])translate([0,0,-my_horn_height])dynamixel_xl330();
      }
    rotate([0,0,-90])translate([0,0,my_motor_height/2+3.5])cube([my_motor_width+1, my_motor_depth+1, my_motor_height+5],center=true);
      for(i=[5:5:85]){
	rotate([i,0,0])translate([0,0,45])rotate([0,90,0])cylinder(d=3.25, h=100, $fn=30,center=true);
	rotate([i,0,0])translate([0,0,35])rotate([0,90,0])cylinder(d=3.25, h=100, $fn=30,center=true);
	rotate([i,0, 0])translate([-2.5, 0, 0])cylinder(d=1.5, h=100);
      }
      translate([0,0,-50+.8])cube(100,center=true);
    }
  }
}

my_horn_height = 2.8;
my_horn_diameter = 16;
my_motor_width = 20;           // Width of motor body
my_motor_depth = 34;           // Depth of motor body
my_motor_height = 23;        // Height of motor body (excluding horn)
my_shaft_offset_from_top = 9.5; // Distance from top of motor to shaft center
//rotate([-90,0,0])color("grey")translate([0, -35, 0])cube([10, 10, 100], center=true);
module dynamixel_motor_mount(){
  difference(){
    dynamixel_motor_mount_arc();
    rotate([0,0,-90])
      scale([1,1,.5])translate([0,0,5])rotate([0,180,180])dynamixel_mounting_screws();
  }
  //rotate([0,180,0])translate([0,0,-my_horn_height])dynamixel_xl330();
  rotate([0,0,-90])
  rotate([0,180,180])
    difference(){
    translate([0,-7.5, 1-my_horn_height])color("red")cube([my_motor_width+4, my_motor_depth+4, 2], center=true);
    cylinder(d=18, h=100, center=true);
    translate([0,0,-1.8-1])dynamixel_mounting_screws();
  }
}
dynamixel_motor_mount();
//rotate([0,180,90])translate([0,0,-my_horn_height])dynamixel_xl330();

module wedge(h, r, a){
  translate([0,0,-h/2])rotate_extrude(angle=a, $fn=100)square([r, h]);
}

module arc(h, outside_r, a, inside_r){
  difference(){
    wedge(h, outside_r, a);
    rotate([0,0,-1])wedge(h+2, inside_r, a+2);
  }
}

module inclination_support(){
  L = 73;
  difference(){
    translate([0,0,50]){
      difference(){
	translate([-10, -7, 0])cube([5, 14, L], center=false);
	translate([0,0,-1])cube([10, 10, 25], center=true);
	translate([0,0,5])rotate([0, -90, 0])cylinder(d=3.5, h=30, $fn=30);
	translate([0,0,-5])rotate([0, -90, 0])cylinder(d=3.5, h=30, $fn=30);
      }
    }
    rotate([0, 90, 0])cylinder(r=50, h=100, center=true, $fn=360);
    translate([-10, 0, 70])cylinder(d=1, h=10, $fn=100);
  }
}
//color("blue")inclination_support();
//cylinder(d=my_horn_diameter, h=my_horn_height);
