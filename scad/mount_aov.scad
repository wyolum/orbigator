/*
 * AoV Motor Mount and Inclination Support
 */

include <common.scad>
include <motor_dynamixel.scad>

// Internal helper for mount geometry
module wedge(h, r, a){
  translate([0,0,-h/2])rotate_extrude(angle=a, $fn=100)square([r, h]);
}

module arc(h, outside_r, a, inside_r){
  difference(){
    wedge(h, outside_r, a);
    rotate([0,0,-1])wedge(h+2, inside_r, a+2);
  }
}

module dynamixel_motor_mount_arc(){
  union(){
    translate([-2.5-5, 0, 0])
      difference(){
      union(){
	rotate([-30, 0, 0])rotate([0, -90, 180])wedge(5, 75, 120);
      }
      translate([-5, -30, 0])cube([10, 60, 11]);
      rotate([0, 90, 0])rotate([0, 0, 270-31])wedge(10, 35, 31);
      rotate([0,90,0])rotate([0,0,180-0])arc(10, 53, 85, 50);
      rotate([0,90,0])rotate([0,0,180-0])arc(10, 68, 85, 65);
      translate([0, 0, 66.5])rotate([0, -90, 0])
	cylinder(d=3.0, h=20, $fn=30, center=true);
      translate([0, 0, 51.5])rotate([0, -90, 0])
	cylinder(d=3.0, h=20, $fn=30, center=true);
      translate([-50, 9, 0])cube(100);
      translate([-50, -100, -98.5])cube(100);
      rotate([85,0,0])translate([0, 0, 66.5])rotate([0, -90, 0])
	cylinder(d=3.0, h=20, $fn=30, center=true);
      rotate([85,0,0])translate([0, 0, 51.5])rotate([0, -90, 0])
	cylinder(d=3.0, h=20, $fn=30, center=true);
      translate([0,2,20])
	rotate([0,90,0])cylinder(d=7, $fn=30, h=50, center=true);

      // make tick marks
      for(theta=[0:5:85]){
	rotate([theta,0, 0])translate([-2.5, 0, 71])cylinder(d=1, h=100);
	rotate([theta,0, 0])translate([-2.5, 0, 47.5])cylinder(d=.5, h=2.5);
      }
      for(theta=[0:15:85]){
	rotate([theta,0, 0])translate([-2.5, 0, 68])cylinder(d=1, h=100);
	rotate([theta,0, 0])translate([-2.5, 0, 46])cylinder(d=.5, h=4);
      }
      for(theta=[0:1:85]){
	rotate([theta,0, 0])translate([-2.5, 0, 73])cylinder(d=1, h=100);
	rotate([theta,0, 0])translate([-2.5, 0, 49.])cylinder(d=.5, h=1.5);
      }
    }
  }
}

module dynamixel_motor_mount(){
  difference(){
    dynamixel_motor_mount_arc();
    rotate([0,0,-90])
      scale([1,1,.5])translate([0,0,5])rotate([0,180,180])
      dynamixel_mounting_screws();
  }
  rotate([0,0,-90])
  rotate([0,180,180])
    difference(){
    translate([0,-7.5, 1-horn_height])color("red")
      cube([motor_width+4, motor_depth+4, 2], center=true);
    cylinder(d=18, h=100, center=true);
    translate([0,0,-1.8-1])dynamixel_mounting_screws();
  }
}
dynamixel_motor_mount();


module inclination_support(){
  difference(){
    translate([0,0,50]){
      difference(){
	translate([-5, 0, 0])cube([10, 14, 20], center=true);
	translate([0,0,-1])cube([10, 10, 25], center=true);
	translate([0,0,5])rotate([0, -90, 0])cylinder(d=3.5, h=30, $fn=30);
	translate([0,0,-5])rotate([0, -90, 0])cylinder(d=3.5, h=30, $fn=30);
      }
    }
    rotate([0, 90, 0])cylinder(r=50, h=100, center=true, $fn=360);
    translate([-10, 0, 70])cylinder(d=1, h=10, $fn=100);
  }
}

if ($show_demo) {
    dynamixel_motor_mount();
    translate([0,0,50]) inclination_support();
}
