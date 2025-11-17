inch = 25.4;

globe_d = 13 * inch;
globe_r = globe_d/2;
globe_thickness = 2;
globe_ir = globe_r - globe_thickness;


height = 14;

RR = 70;
rr = RR - 40;
dd = 8; // magnet support offset from globe_ir

flange_d = 23;
um3_tol = .1;
penny_d = .75 * inch + um3_tol;
penny_t = .06 * inch;

module penny_compartment(dd){
  difference(){
    hull(){
      translate([0,0,0])cylinder(d=flange_d + 4, h=height);
      translate([-dd,0,0])cylinder(d=penny_d + 4, h=height);
    }
    translate([0,0,-2])translate([-dd,0,0])cylinder(d=penny_d, h=height);
    translate([0,0,-2])translate([-dd,0,0])cylinder(d=penny_d * .9, h=height * 2);
  }
  difference(){
    cylinder(d=flange_d + 4, h=.2);
    translate([0,0,-1])cylinder(d=penny_d - .2, h=3);
  }
}

module aov_arm(){
  rotate([0,0,180]){
    difference(){
      union(){
	hull(){
	  cylinder(d=flange_d + 4, h=height);
	  translate([globe_ir-1,-2,0])cube([.1,4,height]);
	}
	penny_compartment(70);
      }
      translate([0,0,-1])cylinder(h=height-1, d=flange_d);
      translate([0,0,-1])cylinder(h=height*2, d=10);
      for(i=[1:4]){
	rotate([0,0,45 + 90 * i])translate([8,0,0])cylinder(d=3.5, h=30, $fn=30);
      }
      translate([0,0,8])rotate([90,0,0])cylinder(d=5, h=40, $fn=30, center=true);
    }

    intersection(){
      difference(){
	cylinder(r=globe_ir, h=height, $fn=50);
	translate([0,0,-1])cylinder(r=globe_ir-2, h=height+2, $fn=50);
	rotate([90,0,0])translate([0,8,0])cylinder(d=5, h=30, $fn=30);
	rotate([0, 0, 180+2.6])translate([-200, 0, 3.4])
	  rotate([0, 90, 0])cylinder(d=3.5, h=100, $fn=30);
	rotate([0, 0, 180-2.6])translate([-200, 0, 3.4])
	  rotate([0, 90, 0])cylinder(d=3.5, h=100, $fn=30);
      }
      translate([100,0,0])cube([200, 25, 100], center=true);
    }
  }
}
aov_arm();
//penny_compartment(0);
