include <MCAD/units.scad>
include <MCAD/materials.scad>
include <MCAD/stepper.scad>


//color("red")motor(Nema14, NemaShort, dualAxis=false)

module kevin_shaft(){
  intersection(){
    cylinder(d=5, h=10, $fn=20);
    cube([4, 10, 100], center=true);
  }
}
module kevin_gear_motor(){
  $fn=30;
  translate([0,0,0])rotate([0,0,-90]){
    color("blue")translate([0,-19,1])cube([14.6,10,2],center=true);
    color("grey")translate([0, -8, 0])cylinder(d=28, h=20);
    color("black")translate([0,0,-1.5])cylinder(d=10, h=1.5);
    color("silver")translate([0,0,-10])kevin_shaft();
    color("grey")difference(){
      union(){
	translate([-35/2, -8, 0])cylinder(d=7, h=1);
	translate([+35/2, -8, 0])cylinder(d=7, h=1);
	translate([0,-8,.5])cube([35, 7, 1], center=true);
      }
      cylinder(d=7, h=1);
      translate([ 35/2, -8, 0])translate([0,0,-1])cylinder(d=5, h=3);
      translate([-35/2, -8, 0])translate([0,0,-1])cylinder(d=5, h=3);
    }
  }
}
module kevin_motor_mount(){
  union(){
    translate([-3.0-5, 0, 0])difference(){
      union(){
	rotate([-30, 0, 0])rotate([0, -90, 180])wedge(7, 50, 120);
	translate([-3.5,-3,1])cube([7, 30, 42]);
      }
      
      translate([0,35/2,-10])cylinder(d=3.5, h=20, $fn=20);
      translate([0,-35/2,-10])cylinder(d=3.5, h=20, $fn=20);
      translate([-10,35/2,5])cube([100, 5.7, 2.5], center=true);
      translate([-10,-35/2,5])cube([100, 5.7, 2.5], center=true);
      cube([35,29,43], center=true);
      rotate([0,90,0])rotate([0,0,180-0])arc(10, 45, 85, 42);
      rotate([0,90,0])rotate([0,0,180-0])arc(10, 35, 85, 32);
      translate([0, 0, 33.5])rotate([0, -90, 0])
	cylinder(d=3.0, h=20, $fn=30, center=true);
      translate([0, 0, 43.5])rotate([0, -90, 0])
	cylinder(d=3.0, h=20, $fn=30, center=true);
      translate([-50, 25, 0])cube(100);
      translate([-50, -100, -99])cube(100);
      translate([0,2,20])
	rotate([0,90,0])cylinder(d=7, $fn=30, h=50, center=true);

      // make tick marks
      translate([-1, 0, 0]){
	for(theta=[0:5:85]){
	  rotate([theta,0, 0])translate([-2.5, 0, 71])cylinder(d=1, h=100);
	  rotate([theta,0, 0])translate([-2.5, 0, 47.5])cylinder(d=.5, h=2.5);
	}
	for(theta=[0:15:85]){
	  rotate([theta,0, 0])translate([-2.5, 0, 68])cylinder(d=2, h=100);
	  rotate([theta,0, 0])translate([-2.5, 0, 0])cylinder(d=1.5, h=100);
	}
      }
    }
  }
}
//kevin_gear_motor();
kevin_motor_mount();

module nema11(){
  size = NemaShort;
  difference(){
    translate([0,0,0]) motor(Nema11, size, dualAxis=false);
    translate([-500, -500, -1000.1])cube(1000);
  }
  
  $fn=100;
  rotate([0, 0, 90])
    translate([0, 0, -17.8])
    color("silver")difference(){
    cylinder(d=5, h=17.8);
    translate([0, -2.25, 0])
      translate([0, 0, 17.8/2])cube([5, .5, 17.8], center=true);
  }
}

module wedge(h, r, a){
  translate([0,0,-h/2])rotate_extrude(angle=a, $fn=100)square([r, h]);
}

module arc(h, outside_r, a, inside_r){
  difference(){
    wedge(h, outside_r, a);
    rotate([0,0,-1])wedge(h+2, inside_r, a+2);
  }
}

module old_aov_motor_mount(){
  translate([0,0,0]){
    translate([0, 0, 12.5])
      cube([12, 29, 5], center=true);
    translate([0, 12, 30])
      cube([12, 5, 30], center=true);
    translate([0, 0, 23])
      rotate([-45, 0, 0])
      translate([0,0,1])cube([12, 5, 32], center=true);
  }
}

module aov_motor_side_rail_base(){
  translate([(10+3)/2, 0, -10])
    rotate([0, 90, 0])
    difference(){
    cylinder(d=150, h=3, center=true, $fn=100);
    //cylinder(d=70, h=5, center=true);
    translate([0, 0, 0])rotate([0, 0, 270-45])wedge(5, 40, 45);
    translate([-9, -500, -500])cube(1000);
    translate([-500, 17, -500])cube(1000);
    translate([-28.25, -28.25, -500])cube(1000);
    rotate([0,0,170])arc(10, 53, 85, 50);
    rotate([0,0,170])arc(10, 68, 88, 65);
  }
}
module aov_side_rail(){
  difference(){
    aov_motor_side_rail_base();
    aov_motor_mount();
  }
}
module aov_motor_case(){
  ss = 23/2;
  aov_side_rail();
  mirror([1, 0, 0])aov_side_rail();
}

module worm_gear_stepper(){
  $fn=30;
  hole_sep = 8.5;
  hole_diam = 2;
  
  rotate([90, 0, 180]){
    color("silver")
    difference(){
      translate([-6, 0, -14])
	cube([12, 10, 18]);
      translate([hole_sep/2, 0, 4 - 1.75])
	rotate([-90, 0, 0])
	translate([0, 0, -1])
	cylinder(d=hole_diam, h=12);
      translate([-hole_sep/2, 0, 4 - 1.75])
	rotate([-90, 0, 0])
	translate([0, 0, -1])
	cylinder(d=hole_diam, h=12);
    }
    color("silver")
      rotate([90, 0, 0])
      translate([0, 0, 0])
      cylinder(d=3, h=8);
    color("grey")translate([0, 5, -28.6+4])
      cylinder(d=10, h=10.6);
    color("black")translate([-6, 0, -28.6+2])
      cube([1, 10, 10.6]);
  }
}
//aov_motor_case();
//nema11();

//translate([0,0,1])worm_gear_stepper();
// motor_model.scad
// Enhanced parametric OpenSCAD model of the 10×10.5×28.6 mm D‑shaft BLDC stepper+gearbox
// Dimensions and mounting holes per provided diagram (units: mm)

//aov_side_rail();
//aov_motor_mount();

module aov_motor_mount(){
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
    difference(){
      translate([-2,-16+10,13.5+1])cube([16, 30, 7], center=true);
      translate([4.25,2.25,-20])cylinder(d=2, h=40, $fn=30);
      translate([-4.25,2.25,-20])cylinder(d=2, h=40, $fn=30);
    }
    rotate([-5, 0, 0])
      translate([-7.5, -51.5, 0])
      difference(){
      rotate([0, 90, 0])
	difference(){
	cylinder(d=7, h=5, $fn=30, center=true);
	cylinder(d=3, h=7, $fn=30, center=true);
	translate([-5,0,0])cube(10, center=true);
      }
    }
  }
}

module inclination_support(){
  difference(){
    translate([0,0,84]){
      difference(){
	translate([-5, 0, 0])cube([10, 14, 20], center=true);
	translate([0,0,-1])cube([10, 10, 25], center=true);
	translate([0,0,5])rotate([0, -90, 0])cylinder(d=3.5, h=30, $fn=30);
	translate([0,0,-5])rotate([0, -90, 0])cylinder(d=3.5, h=30, $fn=30);
      }
    }
    rotate([0, 90, 0])cylinder(r=75, h=100, center=true, $fn=360);
    translate([-10, 0, 70])cylinder(d=1, h=10, $fn=100);
  }
}
//color("blue")inclination_support();
//aov_motor_mount();
