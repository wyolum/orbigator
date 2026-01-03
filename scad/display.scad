/*
 * Display and UI Components
 */

include <common.scad>

module tophat_button_mount(){
  h = 4;
  difference(){
    cylinder(d=8, h=h);
    translate([0,0,-1])cylinder(d=5, h=h+2);
  }
}

module tophat_button(){
  color("black")translate([0,0,-4]){
    cylinder(d=4.5, h=10);
    cylinder(d=5.5, h=5);
  }
}

module side_panel(){
  rotate([90, 0, 0])linear_extrude(2, center=true)
    polygon([[40, 2], [40, 29], [130-50, 29], [199-50, 17], [199-50, 2]]);
}

module inside_box(){
  hull(){
    color("red")translate([0,-40,-174])side_panel();
    color("red")translate([0, 40,-174])side_panel();
  }
}

module display_extension(){
  boost = 15.55; 
  translate([170-50, 0, -base_z_offset+boost])rotate([0,10,0])translate([0,0,-1.89]) {
    // display_spacers(); // from electronics.scad
    translate([-13,21,2])tophat_button_mount();
    translate([ 13,21,2])tophat_button_mount();
  }
  translate([0,0,.5])difference(){
    union(){
      minkowski(){
	inside_box();
	cube(4, center=2);
      }
      translate([170-50, 0, -base_z_offset])rotate([0,10,0])translate([0,0,-1.89])
	translate([-30, 0,1.5])rotate([0,90,0])rotate([0, 0, 45]){
	cube([2, 2, 12],center=true);
	rotate([0,0,45])translate([0,.5,6])cylinder(d1=2, d2=0, h=2, $fn=4);
      }
    }
    inside_box();
    translate([0,0,-5])inside_box();
    translate([-5,0,0])inside_box();
    translate([-5,0,-5])inside_box();
    cylinder(r=R+10, h=2 * globe_d, center=true);

    translate([190-50,0,-base_z_offset+5])rotate([0,100,0])cylinder(d=7, h=40, center=true);//power outlet
    // translate([170-50, 0, -base_z_offset+boost])rotate([0,10,0])mounting_screws();
    translate([170-50, 0, -base_z_offset+boost])rotate([0,10,0])translate([4-30/2,-55/2,-30/2])cube([30-11.25, 55-21, 30], center=false);
    translate([170-50, 21, -base_z_offset+boost])rotate([0,10,0])cylinder(d=16, h=20, center=true);
    translate([170-50, 21, -base_z_offset+boost])rotate([0,10,0])cube([12.5, 12.5, 100], center=true);

    // button holes
    translate([170-50, 21, -base_z_offset+boost])rotate([0,10,0])translate([-13, 0, -2.5])cylinder(d=5., h=10,center=true);
    translate([170-50, 21, -base_z_offset+boost])rotate([0,10,0])translate([ 13, 0, -2.5])cylinder(d=5., h=10,center=true);
  }
  translate([0, 0, -base_z_offset-5.9]){
    difference(){
      translate([50, 0, 0])cube([20, 85, 4], center=true);
      cylinder(r=R+10, h=100, center=true);
      translate([80,0,2])cube([100, 15, 4],center=true);
    }
    translate([150,42,-2])
    intersection(){
      rotate([0,0,45])cube([inch, inch, 4],center=true);
      rotate([0,0,180])cube([inch, inch, 4]);
    }
    mirror([0,1,0])
    translate([150,42,-2])
    intersection(){
      rotate([0,0,45])cube([inch, inch, 4],center=true);
      rotate([0,0,180])cube([inch, inch, 4]);
    }
  }
}

module display_panel(){
  rotate([0,0,0])translate([globe_d/2+5,0,24])rotate([0, 10, 0]){
    difference(){
      cube([70, 80, 2], center=true);
    }
  }
}

if ($show_demo) {
    display_extension();
}
