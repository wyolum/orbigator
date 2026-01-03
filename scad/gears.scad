/*
 * Gears for Orbigator
 */

include </home/justin/code/BOSL2/std.scad>
include </home/justin/code/BOSL2/gears.scad>
include <common.scad>

// 2) Generate a spur gear:
module drive_gear(shaft_diam=5.4){
  color("grey")
    difference(){
    union(){
      rotate([0, 0, 0])
	spur_gear(circ_pitch=pitch, teeth=n, thickness=h,
		  shaft_diam=shaft_diam,
		  herringbone=false, helical=0);
      //color("grey")translate([0, 0, -h/2-3])cylinder(d=30, h=3);
      translate([0, -2.30, 1])
	color("black")cube([5, 1, h+2], center=true);
      translate([0,0,h/2])difference(){
	cylinder(r=8, h=2);
	translate([0,0,-1])cylinder(d=shaft_diam, h=4);
      }
    }
    rotate([0, 0, 220])translate([2.5, 0, -50])cylinder(d=1, h=100);
    mirror([1, 0, 0])
      rotate([0, 0, 220])translate([2.5, 0, -50])cylinder(d=1, h=100);
    translate([0, 0,2.76])cylinder(d1=0 + shaft_diam - 5.3,
				   d2=6.5 + shaft_diam - 5.3, h=3.25);
    translate([0, 0,-4.1])cylinder(d2=0 + shaft_diam - 5.3,
				   d1=6.5 + shaft_diam - 5.3, h=3.25);
  }
}

module idler_gear(){
  radius = 11 * 2 * pitch / PI / 2;
  translate([0, -(R-radius), -140])difference(){
    union(){
      spur_gear(circ_pitch=pitch, teeth=11 * 2, thickness=7,
		herringbone=false, helical=0);
      translate([0,0,7/2])cylinder(d=20, h=2);
    }
    translate([0,0,5-2])cylinder(d=15, h=6, center=true);
    cylinder(d=5.3, h=20, center=true);
  }
}

module idler(){
  translate([0, r, -4.])
    difference(){
    cylinder(d1=12, d2=8, h=2);
    translate([0, 0, -1])cylinder(d=5, h=4);
  }    
}

module Ring(){
  difference(){
    for(theta = [0, 90, 180, 270]){
      rotate([0, 0, theta])
	translate([R+2.25, 0, -base_z_offset - 5])cylinder(d=4, h=6, $fn=4);
    }
    cylinder(r=R+2.25, h=350, center=true);
  }
  translate([0,0,-base_z_offset]){
    translate([0,0,-h/2-3])
      difference(){
      translate([0,0,-2])cylinder(r=r + 10 + 3+.5, h=5);
      translate([0, 0, -3])cylinder(r=r + 13/2, h=h + 3 + 2);
    }
    
    difference(){
      translate([0,0,-2])ring_gear(circ_pitch=pitch,teeth=N,thickness=6);
      translate([0,0,-5])cylinder(r1=r+7.5, r2=r+7.5-5 , h=5);
    }
  }
}

if ($show_demo) {
    drive_gear();
    translate([40,0,0]) Ring();
}
