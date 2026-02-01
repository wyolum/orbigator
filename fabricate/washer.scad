D = 16;
d = 3.5;
h = 3;
$fn = 50;

difference(){
  cylinder(d=D, h=h, center=true);
  cylinder(d=d, h=h+2, center=true);
}
