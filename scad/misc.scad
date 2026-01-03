/*
 * Miscellaneous Mechanical Components
 */

include <common.scad>

// Bearing model
module bearing(){
  color("silver")difference(){
    cylinder(d=13, h=5);
    translate([0,0,-1])cylinder(d=4.6, h=7);
  }
}

// Pivot and arm parts from spring_ring.scad
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

// Torus module
module torus(d=10, thickness=4,res=20){
    rotate_extrude($fn=res) {
        translate([d, 0]) circle(thickness, $fn=res);
    }
}

// Weight hole for ballast
module weight_hole(){
  sphere(d=7);
  cylinder(d=6, h=20);
}

// Spring from spring.scad
module spring(){
  H = 2. * inch;
  D_spring = 3 * inch / 8;
  d_spring = .9;
  
  translate([0, 0, -H/2-(D_spring+d_spring)/2]){
    translate([0, 0, (D_spring + d_spring) / 2])rotate([90, 0, 0])
      torus(D_spring/2, d_spring/2, res=50);
    
    translate([0, 0, H+(D_spring+d_spring)/2])rotate([90, 0, 0])
      torus(D_spring/2, d_spring/2, res=50);
    
    translate([0,0,D_spring-d_spring])
      for(i=[1:47]){
	translate([0, 0, i * d_spring])torus(D_spring/2, d_spring/2, res=50);
      }
  }
}

// D-shaft module
module d_shaft(D, d_flat, h_shaft){
  difference(){
    cylinder(d=D, h=h_shaft, $fn=30);
    translate([D/2.5,-d_flat / 2, -1])cube([d_flat, d_flat, h_shaft + 2]);
  }
}

if ($show_demo) {
    bearing();
    translate([20,0,0]) spring();
    translate([40,0,0]) pivot();
}
