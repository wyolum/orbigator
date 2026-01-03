/*
 * Base Components for Orbigator
 */

include <common.scad>
include <motor_dynamixel.scad>

module foot(){
  translate([0, 0, -18])
    difference(){
    cylinder(d1=20, d2=15, h=10);
    translate([0,0,-1])cylinder(d=4.5, h=12);
    translate([0,0,-1])cylinder(d=10, h=4);
  }
}

module feet(){
  rotate([0,0,30])
    for(theta=[0, 60, 120, 180, -120, -60]){
    translate(r *  [sin(theta), cos(theta), 0])foot();
  }
}

module base_arm(){
  translate([0, 0, -18])
    difference(){
    hull(){
      cylinder(d=40, h=8);
      translate([0, -r, 0]) cylinder(d=15, h=8);
    }
    translate([0,-r,-50])cylinder(d=10, h=100);
  }
}

module base_arms(){
  rotate([0,0,30])
    for(theta=[0, 60, 120, -180, 240, -60]){
    rotate([0, 0, theta])base_arm();
  }
}

module gear_support(){
  translate([55,0,-18])rotate([0,-90,0])difference(){
    cylinder(d=16.3+1.8, $fn=30, h=5, center=true);
    translate([-10,0,0])cube([20, 20, 6],center=true);
  }
}

module RingLock(){
  color("red")translate([0, -r, -146])difference(){
    cylinder(d=16, h=2);
    translate([0,0,-1])cylinder(d=4.5, h=4);
  }
}

module new_base_assy(){
  hh = 23;  
  TT = 14;
  RR = R + 8;
  translate([0,0,-globe_r]){
    difference(){
      union(){
	translate([-25/2, -10, h/2+1])cube([25, 45, 10]);
	translate([-35/2, -10, -hh])cube([35, 25, hh+10]);
	rotate([0,0,30])gear_support();
	rotate([0,0,-90])gear_support();
	rotate([0,0,-210])gear_support();
	// front post to clamp sun gear
	translate([0,-r, -24])cylinder(d=10, h=18, center=false);
	translate([0,-r, -24+18])cylinder(d1=8, d2=8, h=7.1, center=false);
      }
      translate([0, r, -50])cylinder(d=22, h=100);
      rotate([7, 0, 0])translate([-28/2+2, 15.5, h/2+1-12])cube([28, 70, 10]);
    }
    if(true){// base enclosure
      for(theta=[-30, -90, -160, -120, 90, 30]){ 
	translate([0,0,-17])
	  intersection(){
	  rotate([0,0,theta])translate([2 * RR, 0, 0])cylinder(r=RR, h=12);
	  cylinder(r=RR+2, h=12);
	}
      }
    translate([0,0,-TT-10])difference(){
	cylinder(r=R+11, h=TT+5);
	translate([0,0,-7])
	  translate([0,0,TT])cylinder(r=RR+1, h=16);
    }
  }
  translate([-0,-19,-TT-9]) // arm mount
    difference(){
      cylinder(d=15, h=9);
      translate([0,0,-1])cylinder(d=4, h=11);
    }
  }
  translate([0,0,-globe_r-49.4])cylinder(h=26, r=RR+3);
for(theta=[0,90,180,270]){
  rotate([0,0,theta])translate([RR+3, 0, -globe_r-49.4])rotate([0,0,45])translate([-3/2,-3/2, 0])
    cube([3, 3, 44.4],center=false);
 }
}

module base_with_1010_hole(){
  RR = R + 8;
  difference(){
    new_base_assy();
    translate([0, r, 17.8 - h/2-base_z_offset])
      rotate([0,180,0])dynamixel_mounting_screws();

    cube([10.2, 10.2, 1000],center=true);
    translate([5, 5, 0])cylinder(d=3, h=1000, center=true);
    translate([-5, 5, 0])cylinder(d=3, h=1000, center=true);
    translate([-5, -5, 0])cylinder(d=3, h=1000, center=true);
    translate([5, -5, 0])cylinder(d=3, h=1000, center=true);
    translate([0, 0, -base_z_offset - 24.1])rotate([0,0,45])
      cylinder(d1=20, d2=0, h=20/2, $fn=4);
    translate([0, 0, -base_z_offset + 6])rotate([0,0,45])
      cylinder(d2=20, d1=0, h=20/2, $fn=4);
    translate([0,0,-base_z_offset]){
      // eqx motor cutout
      translate([0,34,41.5])
	cube([motor_width+.5, motor_depth+1, motor_height], center=true);
      // hole for t-slot screw to 1010
      translate([0, 8, -13])rotate([-90, 0, 0])cylinder(d=2.5, h=100);
      translate([0, 8, -13])rotate([-90, 0, 0])cylinder(d=10, h=100);

       // big holes in bottom
       translate([35,0,-50])scale([1,1.7,1])cylinder(d=35, h=100);
       translate([-35,0, -50])scale([1,1.7,1])cylinder(d=35, h=100);
       translate([-15,-35, -50])cylinder(d=20, h=100);
       translate([15,-35, -50])cylinder(d=20, h=100);
       
       translate([0,-r, -50])cylinder(d=4.5, h=100);
       translate([0,r-7, -50])cube([25, 38, 100], center=true);
       translate([0,-r, -30+4])cylinder(d=10, h=5, center=false);

       //pivot mount screw hole
       translate([0, -19, 0])cylinder(d=4.5, h=100, center=true);
       translate([0, -19, -30+4])cylinder(d=10, h=5, center=false);
       translate([50,0,-20])cube([40, 55, 10], center=true); // motor cable slot
    }
  }
}

module glides(){
  ll = (2 * r + 26)/2;
  rotate([0,0,45])
  translate([0,0,-150]){
    difference(){
      translate([0,0,-12.5]){
	rotate([45, 0, 0])translate([ll/2,0,0])cube([ll, 5, 5],center=true);
	translate([ll/2,0,-4])cube([ll, 7, 7],center=true);

	rotate([45, 0, 90])translate([ll/2, 0, 0])
	  cube([ll, 5, 5],center=true);
	rotate([0,0,90])translate([ll/2,0,-4])
	  cube([ll, 7, 7],center=true);
	rotate([45, 0, -135])translate([ll/2, 0, 0])
	  cube([ll, 5, 5],center=true);
	rotate([0,0,-135])translate([ll/2,0,-4])
	  cube([ll, 7, 7],center=true);
    }
      cylinder(r=r+7, h=100, center=true);
    }
  }
}

if ($show_demo) {
    base_with_1010_hole();
}
