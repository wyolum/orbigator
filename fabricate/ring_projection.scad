// 2D projection of just the Ring from full_assembly.scad
// Avoids arduino.scad dependency issues

include </home/justin/code/BOSL2/std.scad>
include </home/justin/code/BOSL2/gears.scad>

$fn=100;

N = 60 * 2;
n = 7 * 2;
pitch = 2.494;
h = 8;

globe_d = 299;
globe_r = globe_d/2;
inch = 25.4;
base_z_offset = 150 - (globe_d - 13 * inch)/2;

R = N * pitch / PI / 2;
r = R - n * pitch / PI / 2;

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

// Project onto XY plane
projection(cut = false) {
  translate([0,0,17]) Ring();
  // Add bearing contact circle
  translate([0, 0, -base_z_offset]) 
    cylinder(r = r + 13/2, h = 0.1);
}
