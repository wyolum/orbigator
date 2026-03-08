// 125 total length
// 87 handle length
$fn=50;
module sharpie(){
  h1 = 8.5;
  h2 = 78.5;
  h3 = 23;
  d1 = 5;
  d2 = 10.8;
  d3 = 12.4;
  d4 = 10.6;
  d5 = 10;
  cylinder(h=h1, d2=d2, d1=d1);
  translate([0,0,h1])cylinder(h=h2, d1=d2, d2=d3);
  color("black")translate([0,0,h1+h2])cylinder(h=h3, d1=d4, d2=d5);
  color("black")translate([0,0,h1+h2+h3])sphere(d=d5);
  color("black")translate([0,0,h1+h2+h3])cylinder(d1=5, d2=2, h=15);
}

color("yellow")difference(){
  union(){
    cylinder(d=18, h=15);
    translate([0,3,15/2])cube([8, 20, 15], center=true);
    translate([0,13,15/2])rotate([0,90,0])cylinder(h=8, d=15, center=true);
  }
  translate([0,0,-30])scale([1.01, 1.01, 1])sharpie();
  translate([0,20,0])cube([2, 40, 40], center=true);
  translate([0,13,15/2])rotate([0,90,0])cylinder(d=3.5, h=20, center=true, $fn=30);
}

sharpie();
