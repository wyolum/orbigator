$fn=40;

flange_d = 22;
collar_d = 10;
hole_d = 3;

hole_w = 11.3;
collar_h = 12;
flange_h = 2;

hole_r = 8;

module m3_flange(){
  translate([0,0,collar_h])
  rotate([180, 0, 0])
  color("silver")
  difference(){
    union(){
      cylinder(d=flange_d, h=flange_h);
      cylinder(d=collar_d, h=collar_h);
    }
    translate([0,0,-1])cylinder(d=hole_d, h=collar_h + 2);
    for(i=[1:4]){
      rotate([0, 0, 90 * i])translate([hole_r, 0, -1])cylinder(d=hole_d, h=collar_h + 2);
    }
    rotate([0,0,-45])translate([0, 0, 8])rotate([0, 90, 0])cylinder(d=hole_d, h=collar_h + 2);
  }
}

m3_flange();
