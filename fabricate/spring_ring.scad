include </home/justin/code/BOSL2/std.scad>
include </home/justin/code/BOSL2/gears.scad>
use <spring.scad>

$fn=360;
N = 60 * 2;
n = 7 * 2;
pitch = 2.5;

h = 8;

R = N * pitch / PI / 2;
r = R - n * pitch / PI / 2;
echo("r=", r);
module Ring(){
  difference(){
    for(theta = [0, 90, 180, 270]){
      rotate([0, 0, theta])
	translate([R+2.25, 0, -155])cylinder(d=4, h=9, $fn=4);
    }
    cylinder(r=R+2.25, h=350, center=true);
  }
  translate([0,0,-150]){

    translate([0,0,-h/2-3])
      difference(){
      translate([0,0,-2])cylinder(r=r + 10 + 3, h=5);
      translate([0, 0, -3])cylinder(r=r + 13/2, h=h + 3 + 2);
    }
    
    difference(){
      ring_gear(circ_pitch=pitch,teeth=N,thickness=h);
    }
    
  }
}

module bearing(){
  translate([0, 0, -4])color("silver")difference(){
    translate([0, 0, -5])cylinder(d=13, h=5);
    translate([0,0,-5-1])cylinder(d=4.6, h=7);
  }
}

// 2) Generate a 6-tooth spur gear:
module drive_gear(){
  color("grey")
    difference(){
    union(){
      rotate([0, 0, 0])
	spur_gear(circ_pitch=pitch, teeth=n, thickness=h, shaft_diam=5.3,
		  herringbone=false, helical=0);
      //color("grey")translate([0, 0, -h/2-3])cylinder(d=30, h=3);
      translate([0, -2.25, 0])
	color("black")cube([5, 1, h], center=true);
    }
    rotate([0, 0, 233])translate([2.5, 0, -50])cylinder(d=1, h=100);
    mirror([1, 0, 0])
      rotate([0, 0, 233])translate([2.5, 0, -50])cylinder(d=1, h=100);
    translate([0, 0,.76])cylinder(d1=0, d2=6.5, h=3.25);
    translate([0, 0,-4.1])cylinder(d2=0, d1=6.5, h=3.25);
  }
  //cylinder(d=8, h=20);
}

module pivot(){
  translate([0, 0, -9])difference(){
    cylinder(d=10, h=5);
    translate([0,0,-1])cylinder(d=4.5, h=7);
  }
}

module arm_part(l){
  rotate([0, 0, 0])hull(){
    pivot();
    translate([0, l, 0])pivot();
  }
}

module torus(d=10, thickness=4,res=20){
    rotate_extrude($fn=res) {
        translate([d, 0]) circle(thickness, $fn=res);
    }
}

module arm_half(ll){
  translate([-14, 0, 0]){
    translate([0,0,-5])difference(){
      arm_part(ll);
      translate([0,0,-20])  cylinder(d=4.5, h=40);
    }
    translate([0,ll,-5])rotate([0,0,90])arm_part(7);
  }
  
  translate([-22,36,-14]){
    rotate([0,0,-45])
      hull(){
      cylinder(d=13, h=5);
      translate([0, -10, 0])cylinder(d=10, h=5);
  }
  rotate([0,0,-45])
    translate([0,-10,0])difference(){
    cylinder(d=7, h=5+4);
    translate([0,0,7])torus(d=7/2, thickness=1,res=50);
    }
  }
}
module spring_arms_pre(){
  ll = 40;
  difference(){
    color("red")arm_half(ll);
    translate([-14,0,-5-4-2.5])  cylinder(d=20, h=50);
    rotate([0,0,120])translate([r, 0, -15])cylinder(d=4.5, h=20);
    rotate([0,0,120])translate([r, 0, -15])cylinder(d=8, h=4);
  } 
  translate([-14, 0, -12])difference(){
    cylinder(d=6.5, h=8);
    translate([0,0,-1])cylinder(d=4.5, h=12);
  }
  translate([0, 0, 0])difference(){
    color("blue")union(){
      mirror([0,1,0])arm_half(ll);
      translate([-14, 0, -9])cylinder(d=10, h=5);
    }
    translate([-14, 0 ,-14])cylinder(d=6.5+.2, h=20);
    translate([-14,0,-5-4-2.5-10])  cylinder(d=20, h=10);
    rotate([0,0,-120])translate([r, 0, -15])cylinder(d=4.5, h=20);
    rotate([0,0,-120])translate([r, 0, -15])cylinder(d=8, h=4);
  }
}
module spring_arms(){
  translate([-5,0,0])spring_arms_pre();
}
module idler_gear(){
  color("grey")
    difference(){
    union(){
      rotate([0, 0, 0])
	spur_gear(circ_pitch=pitch, teeth=n, thickness=h, shaft_diam=4.5,
		  herringbone=false, helical=0);
      //color("grey")translate([0, 0, -h/2-3])cylinder(d=30, h=3);
    }
  }
  //cylinder(d=8, h=20);
}

module tribase_pre(){
  translate([-19, 0, -10])pivot();
  translate([-19, 0, -11])pivot();
  
  difference(){
    union(){
      difference(){
	translate([0, 0, -20])cylinder(r=r, h=5);
	translate([0, 0, -21])cylinder(r=r-5, h=7);  
      }
      translate([0,0,-20+2.5])cube([2 * r, 5, 5], center=true);
    }
    translate([-19, 0, 0, ])cylinder(d=4.5, h=100,center=true);
    translate([r, 0, 0, ])cylinder(d=4.5, h=100,center=true);
  }
  translate([r, 0, -5])pivot();
  translate([r, 0, -10])pivot();
  translate([r, 0, -11])pivot();
}
module tribase(){
  difference(){
    tribase_pre();
    translate([-19, 0, -11-10])cylinder(d=8, h=4);
    translate([r, 0, -11-10])cylinder(d=8, h=4);
  }
  translate([-r+9, 0, -10])cube([7, 1, 10], center=true);
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

Ring();
glides();
if(false){
  spring_arms();
  color("grey")cube([10, 10, 100], center=true);
  translate([-14, 0, -10])pivot();
  translate([r, 0, 0])rotate([0,0,180/n])drive_gear();
  translate([0,0,150])Ring();
  for(theta=[120, 240]){
    rotate([0,0,theta])
      translate([r, 0, 0])
      bearing();
  }
  color("silver")translate([-28, 0, -5-3])rotate([90, 0, 0])spring();
 }
