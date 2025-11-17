pi = 3.14159;

module m4_nut(){
  d = 6.7 / cos(pi/6);
  difference(){
    cylinder(d=d, h=3, $fn=6);
    translate([0,0,-1])cylinder(d=4.1, h=5, $fn=30);
  }
}
m4_nut();
