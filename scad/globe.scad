/*
 * Globe and Interface
 */

include <common.scad>

module globe(){
  color("blue", alpha=.1)
    difference(){
    sphere(d=globe_d);
    sphere(d=globe_d - 4);
    translate([-500, -500, -base_z_offset-100])cube([1000, 1000, 100]);
  }
}

ring_xyscale = 1.0075;
module globe_interface_ring_start(h_ring){
  scale([ring_xyscale, ring_xyscale, 1]){
    difference(){
      union(){
	cylinder(r=55.6, h=h_ring);
      }
      translate([0,0,-1])cylinder(r=R+2.25, h=h_ring+2);
      for(theta = [0, 90, 180, 270]){
	rotate([0, 0, theta])
	  translate([R+2.25, 0, -1])cylinder(d=4, h=h_ring+2, $fn=4);
      }
      translate([0,0,h_ring-2])difference(){
	cylinder(r=55.7, h=h_ring);
	translate([0,0,-1])cylinder(r=55.6-2, h=h_ring+2);
      }
    }
  }
}

module globe_interface_ring(){
  h_ring = 4;
  scale([ring_xyscale, ring_xyscale, 1])translate([0,0,-base_z_offset-4]){
    globe_interface_ring_start(h_ring=h_ring);
    difference(){
      union(){
	translate([0,0,1])for(theta = [0, 90, 180, 270]){ // bump outs
	  rotate([0, 0, theta])
	    translate([R+6, 0, -1])cylinder(d=4, h=h_ring, $fn=4);
	}
      }
      cylinder(d=106, h=10, center=true);
    }
  }
}

if ($show_demo) {
    globe_interface_ring();
    globe();
}
