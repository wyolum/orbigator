inch = 25.4;

D = 13*inch;
MAGNET_SEP = 7;

module bearing(d=6){
  sphere(d=d, $fn=50);
}

module bearings(d=6){
  sep = MAGNET_SEP;
  translate([-sep, 0, 0])bearing(d);
  translate([ sep, 0, 0])bearing(d);
}

module sled_base(){
  L = 25;
  W = 15;
  H = 6.;
  
  difference(){
    translate([-L/2, -W/2,-1])cube([L, W, H],center=false);
    translate([0, 0,2.9])bearings(7);
    translate([0, 0, -D/2])sphere(d=D, $fn=300);
    translate([MAGNET_SEP, 0, 1.7])cylinder(d=7, h=3, $fn=30);
    translate([-MAGNET_SEP, 0, 1.7])cylinder(d=7, h=3, $fn=30);
    translate([MAGNET_SEP, 0, 1.7])cylinder(d=6, h=10, $fn=30);
    translate([-MAGNET_SEP, 0, 1.7])cylinder(d=6, h=10, $fn=30);
  }
  //color("silver")translate([0,0,2.2])bearings(6);
  //color("silver")cylinder(h=inch, d=1.5, $fn=30);
}

module sled_complete(){
  /*
  translate([-3,-3,inch])rotate([-40, 0, 0])
    rotate([0, 70, 0])scale(30)translate([-28.85, 0, 0])
    color("grey")import("sat_model_2.stl");
  */

  intersection(){
    sled_base();
    scale([1, .55, 1])translate([0,0,-50])cylinder(d=25, h=100);
  }
}

module sled(){
  translate([0, 0, 3.5])
  rotate([0,-90,0])rotate([0, 0, 90])sled_complete();
}
sled();
//color("blue", alpha=.5)    translate([0, 0, -D/2])sphere(d=D, $fn=300);

module magnet(){
  color("silver"){
    cylinder(h=13, d=3, $fn=30);
    minkowski(){
      translate([0,0,.5])
      cylinder(d=10, h=3, $fn=30);
      sphere(d=1, $fn=30);
    }
  }
}

module magnets_up(){
  angle = atan2(MAGNET_SEP, D/2);
  translate([MAGNET_SEP, 0, 0])rotate([180, +angle/2, 0])magnet();
  translate([-MAGNET_SEP, 0, 0])rotate([180, -angle/2, 0])magnet();
}
module magnets(){
  translate([2, 0,3.5])
  rotate([-90,0,90])
  magnets_up();
}

//magnets();
