inch = 25.4;
globe_d = 37.125 * inch / PI;
globe_r = globe_d / 2;
globe_thick = .3 * inch;

module south_pole_1(){
  rotate([180, 0, 0])scale(globe_d / 78.63)
  translate([-62.73, -62.32, 0])import("earthmap_south.stl");
  //color("red")cylinder(d=78.63, h=1, $fn=100);
}

module cutout(){
  translate([0, 0, -globe_r+18])union(){
    cylinder(d=5.3 * inch, h=globe_r, center=false, $fn=360);
    translate([0,0, -globe_r])
      cylinder(d=5.3 * inch + 2, h=globe_r, center=false, $fn=360);
  }
}

module south_pole(){
  difference(){
    intersection(){
      south_pole_1();
      cutout();
    }
    sphere(d=globe_d - globe_thick);
  }
}

N = 60 * 2;
n = 7 * 2;
//pitch = 2.5;
pitch = 2.494;
h = 8;

R = N * pitch / PI / 2;
r = R - n * pitch / PI / 2;
echo("R=", R);
echo("R + 2.25=", R+2.25);
echo("r=", r);

ring_xyscale = 1.0075;
module globe_interface_ring_start(h){
  scale([ring_xyscale, ring_xyscale, 1]){
    difference(){
      union(){
	cylinder(r=55.6 * 2, h=h);
      }
      translate([0,0,-1])cylinder(r=49.8819, h=10);
      for(theta = [0, 90, 180, 270]){
	rotate([0, 0, theta])
	  translate([49.8819, 0, -1])cylinder(d=4, h=10, $fn=4);
      }
      translate([0,0,6])difference(){
	cylinder(r=55.7, h=h);
	translate([0,0,-1])cylinder(r=55.6-2, h=10);
      }
    }
  }
}

intersection(){
  color("red")translate([0,0,-170])scale([1,1,100])globe_interface_ring_start();
  south_pole();
}
