include <arduino.scad>
include </home/justin/code/BOSL2/std.scad>
include </home/justin/code/BOSL2/gears.scad>
use <stepper_motors.scad>
use <sled.scad>
inch = 25.4;
$fn=100;

N = 60;
n = 7;
h = 8;

globe_d = 13 * inch;
globe_r = globe_d/2;

//color("red", alpha=.3)translate([0, 0, 150])sphere(d=inch/2, $fn=12);

// 2) Generate a 6-tooth spur gear:
module drive_gear(){
  rotate([0, 0, ])
    color("black")spur_gear(circ_pitch=5, teeth=n, thickness=h, shaft_diam=5);
  //color("grey")translate([0, 0, -h/2-3])cylinder(d=30, h=3);
  translate([0, -2.25, 0])
    color("black")cube([5, .5, h], center=true);
}


module idler(){
  translate([0, 0, -h/2])
    difference(){
      color("grey")translate([0, 0, -3])cylinder(d=30, h=4);
      translate([0, 0,-50])cylinder(d=4.5, h=100);
      translate([0, 0,-3-1])cylinder(d=8, h=3+1);
  }
}


pitch = 5;

R = N * pitch / PI / 2;
r = R - n * pitch / PI / 2;
echo("r=", r);
module Ring(){
  translate([0,0,-150]){

    translate([0,0,-h/2-3])
      difference(){
      cylinder(r=r + 15 + 3, h=h + 3);
      translate([0, 0, -1])cylinder(r=R+pitch, h=h + 3 + 2);
      translate([0, 0, -1])cylinder(r=r+15, h=3+1);
    }
    
    difference(){
      translate([0, 0, 150])sphere(d=13*INCH);
      translate([-500, -500, 0])cube(1000);
      translate([0, 0, -500])cylinder(h=1000,r=r+15);
    }
    
    
    ring_gear(circ_pitch=pitch,teeth=N,thickness=h);
    
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
    translate([0, r, 17.8 - h/2])nema11();
    translate([0, r, 0])drive_gear();
  }
}

//Ring();

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
  for(theta=[60, 180, -60]){
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
  for(theta=[0, 120, 240]){
    rotate([0, 0, theta])base_arm();
  }
}


module base_assy(){
  dd = 23/2;
  translate([0,0,-150]){
    feet();

    
    difference(){
      translate([-35/2, 0, h/2+1])cube([35, r+17, 10]);
      translate([0, r, -50])cylinder(d=25, h=100);
      translate([dd, r+dd, -50]) cylinder(h=100, d=3);
      translate([-dd, r+dd, -50]) cylinder(h=100, d=3);
      translate([ dd, r-dd, -50]) cylinder(h=100, d=3);
      translate([-dd, r-dd, -50]) cylinder(h=100, d=3);
      translate([ dd, r+dd, -100+dd]) cylinder(h=100, d=5.5);
      translate([ dd, r-dd, -100+dd]) cylinder(h=100, d=5.5);
      translate([-dd, r+dd, -100+dd]) cylinder(h=100, d=5.5);
      translate([-dd, r-dd, -100+dd]) cylinder(h=100, d=5.5);
    }
    
    hh = 23;
    translate([0,0,h/2+1-hh])cylinder(d1=60, d2=35, h=10+hh);
    difference(){
      base_arms();
      translate([0,0,150])sphere(d=13 * inch);
    }
  }
}
module base_with_1010_hole(){
  difference(){
    base_assy();
    cube([10.2, 10.2, 1000],center=true);
    rotate([-90, 0, 0])cylinder(d=2.5, h=100);
    translate([0, 8, 0])rotate([-90, 0, 0])cylinder(d=6, h=100);
    translate([0, 0, -13])rotate([-90, 0, 0])cylinder(d=2.5, h=100);
    translate([0, 8, -13])rotate([-90, 0, 0])cylinder(d=6, h=100);
  }
}
module d_shaft(D, d, h){
  difference(){
    cylinder(d=D, h=h, $fn=30);
    translate([D/2.5,-d / 2, -1])cube([d, d, h + 2]);
  }
}

module aov_arm_base(){
  RR = globe_r/2 + 10;
  echo("RR=", RR);
  rr = RR - 20;
  echo("rr=", rr);
  dd = 8; // magnet support offset from globe_r
  echo("Globe_radius - 8", globe_r - 8);
  hull(){
    translate([0,0,5])cylinder(r=6, h=10,center=true);
    translate([-(globe_r-dd-3), 0, 2.5])cube([6, 6, 5], center=true);
  }
  difference(){
    intersection(){
      difference(){
	cylinder(r=globe_r-dd, h=7);
	translate([0,0,-1])cylinder(r=globe_r-dd-2, h=10);
      }
      translate([-100,0,0])cube([200, 25, 100], center=true);
    }
    rotate([0, 0, 2.6])translate([-160, 0, 3.4])
      rotate([0, 90, 0])cylinder(d=3.5, h=10, $fn=30);
    rotate([0, 0, -2.6])translate([-160, 0, 3.4])
      rotate([0, 90, 0])cylinder(d=3.5, h=10, $fn=30);
  }
  difference(){
    cylinder(r=RR, h=6);
    translate([0,0,-1])cylinder(r=rr, h=8);
    rotate([0, 0, 60])translate([-2 * rr-1, 0, -1])
      cube([4 * rr + 2, 4 * rr + 2, 8]);
    rotate([0, 0, 120])translate([-2 * rr-1, 0, -1])
      cube([4 * rr + 2, 4 * rr + 2, 8]);
  }
  translate([0, -3/2, 0])cube([RR, 3, 6]);
  rotate([0,0,-60])
  translate([0, -3/2, 0])cube([RR, 3, 6]);
  rotate([0,0,60])
  translate([0, -3/2, 0])cube([RR, 3, 6]);
}

module torus(d=10, thickness=4,res=20){
    rotate_extrude($fn=res) {
        translate([d, 0]) circle(thickness, $fn=res);
    }
}

module aov_arm(){
  difference(){
    aov_arm_base();
    translate([0,0,-1])d_shaft(3, 2.5, 10);
    translate([0, 0, -5])torus(d=50, thickness=6);
  }
}
module aov_motor_assy(inc, aov){
  translate([0,0,-140]){
    color("grey")translate([-5,-5,-18])cube([10, 10, 120], center=false);
    translate([0, 0, 150])translate([0, 0, -10])
      rotate([inc, 0, 0])rotate([0, 180, 0]){
      translate([0,0,0])worm_gear_stepper();
      color("coral")aov_motor_mount();
      translate([-10,10,90])rotate([90, 180, 180])arduino();
    }
    translate([0, -3, 140])
      rotate([inc, 0, 0])rotate([0, 0, aov-180]){
      color([.4, .4, .4, 1])aov_arm();
      translate([-globe_r, 0, 0])sled();
      translate([-globe_r, 0, 0])magnets();
    }
  }
}


if(true){
  color("cornflowerblue")Ring();
  eqx_motor_assy();
  color("lightslategrey")base_with_1010_hole();
  idlers();
  aov_motor_assy(55, 50);
  color("blue")rotate([0,180,0])translate([0,0,0])inclination_support();
 }
module globe(){
  color("blue", alpha=.6)
    difference(){
    sphere(d=globe_d);
    sphere(d=globe_d - 4);
    translate([-500, -500, -150-100])cube([1000, 1000, 100]);
  }
}
//globe();
//color("grey")aov_arm();


