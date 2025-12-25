include <arduino.scad>
include </home/justin/code/BOSL2/std.scad>
include </home/justin/code/BOSL2/gears.scad>

use <dynamixel_motor.scad>
use <inclination_aov_mount.scad>
use <flange.scad>
use <sled.scad>
use <spring.scad>
use <spring_ring.scad>
use <dynamixel_aov_arm.scad>
use <main_board.scad>

// Import the STEP file
module pico(){
  import("stls/pi-pico-2w-cad-reference.stl");
}

inch = 25.4;
$fn=100;

N = 60 * 2;
n = 7 * 2;
//pitch = 2.5;
pitch = 2.494;
h = 8;

globe_d = 13 * inch;
globe_r = globe_d/2;

module bearing(){
  color("silver")difference(){
    cylinder(d=13, h=5);
    translate([0,0,-1])cylinder(d=4.6, h=7);
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
//idler_gear();

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
  //cylinder(d=8, h=20);
}


module idler(){
  translate([0, r, -4.])
    difference(){
    cylinder(d1=12, d2=8, h=2);
    translate([0, 0, -1])cylinder(d=5, h=4);
  }    
}

R = N * pitch / PI / 2;
r = R - n * pitch / PI / 2;
echo("r=", r);
module Ring(){
  difference(){
    for(theta = [0, 90, 180, 270]){
      rotate([0, 0, theta])
	translate([R+2.25, 0, -155])cylinder(d=4, h=6, $fn=4);
    }
    cylinder(r=R+2.25, h=350, center=true);
  }
  translate([0,0,-150]){

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

module idlers(){
  translate([0, 0, -151])
    for(i=[1:2:5]){
      translate([r * sin(60 * i), r * cos(60 * i), 0]) idler();
    }
}
module eqx_motor_assy(){
  translate([0,0,-150]){
    //translate([0, r, 17.8 - h/2])nema11();
    translate([0, r, 17.8 - h/2])rotate([0,180,0])dynamixel_xl330();
    translate([0, r, 17.8 - h/2])rotate([0,180,0])dynamixel_drive_shaft();
    translate([0, r, -2.8])drive_gear();
  }
}

// feet
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

module base_assy(){
  dd = 23/2;
  translate([0,0,-150]){
    feet();    
    difference(){
      union(){
	translate([-35/2, 0, h/2+1])cube([35, r, 10]);
	translate([0, r, h/2+1])cylinder(d=40, h=10);
      }
      translate([0, r, -50])cylinder(d=25, h=100);
      translate([dd, r+dd, -50]) cylinder(h=100, d=3.5);
      translate([-dd, r+dd, -50]) cylinder(h=100, d=3.5);
      translate([ dd, r-dd, -50]) cylinder(h=100, d=3.5);
      translate([-dd, r-dd, -50]) cylinder(h=100, d=3.5);
      translate([ dd, r+dd, -100+dd]) cylinder(h=100, d=6.5);
      translate([ dd, r-dd, -100+dd]) cylinder(h=100, d=6.5);
      translate([-dd, r+dd, -100+dd]) cylinder(h=100, d=6.5);
      translate([-dd, r-dd, -100+dd]) cylinder(h=100, d=6.5);
    }
    
    hh = 23;
    translate([0,0,h/2+1-hh])cylinder(d1=60, d2=35, h=10+hh);
    difference(){
      base_arms();
      translate([0,0,150])sphere(d=13 * inch);
    }
  }
}

module RingLock(){
  color("red")translate([0, -r, -146])difference(){
    cylinder(d=16, h=2);
    translate([0,0,-1])cylinder(d=4.5, h=4);
  }
}

module gear_support(){
  translate([55,0,-18])rotate([0,-90,0])difference(){
    cylinder(d=16.3+1.8, $fn=30, h=5, center=true);
    translate([-10,0,0])cube([20, 20, 6],center=true);
  }
}

module new_base_assy(){
  dd = 23/2;
  hh = 23;  
  translate([0,0,-150]){
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
    TT = 14;
    if(true){// base enclosure
      translate([0,0,-TT-10])difference(){
	cylinder(r=R+11, h=TT+5);
	translate([0,0,-7])
	  translate([0,0,TT])cylinder(r=R + 8, h=16);
    }
  }
  translate([-0,-19,-TT-9]) // arm mount
    difference(){
      cylinder(d=15, h=9);
      translate([0,0,-1])cylinder(d=4, h=11);
    }
  }
}

module base_with_1010_hole(){
  dd = 23/2;
  motor_width = 20;           // Width of motor body
  motor_depth = 34;           // Depth of motor body
  motor_height = 23;        // Height of motor body (excluding horn)
  
  difference(){
    new_base_assy();
    translate([0, r, 17.8 - h/2-150])
      rotate([0,180,0])dynamixel_mounting_screws();

    cube([10.2, 10.2, 1000],center=true);
    translate([5, 5, 0])cylinder(d=3, h=1000, center=true);
    translate([-5, 5, 0])cylinder(d=3, h=1000, center=true);
    translate([-5, -5, 0])cylinder(d=3, h=1000, center=true);
    translate([5, -5, 0])cylinder(d=3, h=1000, center=true);
    translate([0, 0, -150 - 24.1])rotate([0,0,45])
      cylinder(d1=20, d2=0, h=20/2, $fn=4);
    translate([0, 0, -150 + 6])rotate([0,0,45])
      cylinder(d2=20, d1=0, h=20/2, $fn=4);
    translate([0,0,-150]){
      // eqx motor cutout
      translate([0,34,25])
	cube([motor_width+.5, motor_depth+1, motor_height], center=true);
      // hole for t-slot screw to 1010
      translate([0, 0, -13])rotate([-90, 0, 0])cylinder(d=2.5, h=100);
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
       translate([50,0,-20])cube([40, 15, 5], center=true); // motor cable slot
    }
  }
}
module d_shaft(D, d, h){
  difference(){
    cylinder(d=D, h=h, $fn=30);
    translate([D/2.5,-d / 2, -1])cube([d, d, h + 2]);
  }
}

module torus(d=10, thickness=4,res=20){
    rotate_extrude($fn=res) {
        translate([d, 0]) circle(thickness, $fn=res);
    }
}

module weight_hole(){
  sphere(d=7);
  cylinder(d=6, h=20);
}

module aov_motor_assy(inc, aov){
  translate([0,0,-140]){
    //color("black")translate([-5,-5,-1000+100])cube([10, 10, 1000], center=false);
    translate([0, 0, 150])translate([0, 0, -10])
      rotate([inc, 0, 0])rotate([0, 180, 0]){
      translate([0,0,0])rotate([0,180,90])translate([0,0,-2.8])dynamixel_xl330();
      color("coral")dynamixel_motor_mount();
      //translate([-10,10,90])rotate([90, 180, 180])arduino();
      //translate([0,10,40])rotate([90, 0, 180])pico();
    }
    translate([0, -3, 140])
      rotate([inc, 0, 0])rotate([0, 0, aov-180]){
      color([.4, .4, .4, 1])aov_arm();
      translate([-globe_r, 0, 0])sled();
      translate([-globe_r, 0, 0])magnets();
    }
  }
}
/*
  difference(){
  outside_box();
  translate([0,0,-4])scale([.98, .98, 1])outside_box();
  sphere(d=globe_d+2);
}
*/
//translate([170, 0, -150])rotate([0,10,0])main_assy();
module inside_box(){
  hull(){
    color("red")translate([0,-40,-174])side_panel();
    color("red")translate([0, 40,-174])side_panel();
  }
}
module outside_box(){
  difference(){
    minkowski(){
      inside_box();
      cube(4, center=2);
    }
    inside_box();
    translate([0,0,-5])inside_box();
    translate([-5,0,0])inside_box();
    translate([-5,0,-5])inside_box();
    sphere(globe_r + 2);
    translate([190-50,0,-165])rotate([0,100,0])cylinder(d=7, h=40, center=true);
    translate([170-50, 0, -150])rotate([0,10,0])mounting_screws();
    translate([170-50, 0, -150])rotate([0,10,0])cube([30, 55, 30], center=true);
    translate([170-50, 20, -150])rotate([0,10,0])cylinder(d=18, h=20, center=true);
  }
}
module side_panel(){
  rotate([90, 0, 0])linear_extrude(2, center=true)
    //polygon([[40, 2], [40, 29], [136, 29], [205, 17], [205, 2]]);
    //polygon([[40, 2], [40, 29], [130, 29], [199, 17], [199, 2]]);
    polygon([[40, 2], [40, 29], [130-50, 29], [199-50, 17], [199-50, 2]]);
}
//outside_box();
module display_panel(){
  rotate([0,0,0])translate([globe_d/2+5,0,24])rotate([0, 10, 0]){
    difference(){
      cube([70, 80, 2], center=true);
      //display_assy();
    }
  }
}
//color("lightslategrey")base_with_1010_hole();

if(false){
  color("cornflowerblue")Ring();
  eqx_motor_assy();
  color("lightslategrey")base_with_1010_hole();
  //aov_motor_assy(65, 350);
  //color("blue")rotate([0,180,0])translate([0,0,0])inclination_support();
  //color("black")translate([0,0,-100])cube([10, 10, 150], center=true);
}
else{
  //Ring();
  //color("lightslategrey")base_with_1010_hole();
  //glides();
  //translate([0,0,-150])rotate([0,0,90])spring_arms();
  //Ring();
 }

module globe(){
  color("blue", alpha=.3)
    difference(){
    sphere(d=globe_d);
    sphere(d=globe_d - 4);
    translate([-500, -500, -150-100])cube([1000, 1000, 100]);
  }
}
color("lightslategrey")base_with_1010_hole();
outside_box();
