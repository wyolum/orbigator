L = 73;
difference(){
  translate([-5, -2.5, 0])cube([10, 3, L+1]);
  translate([0,3.5,50+L])rotate([90,0,0])cylinder(r=50, h=7,center=false, $fn=100);
  translate([0,0,10])rotate([90, 0,0])cylinder(d=3.5, h=100, $fn=30,center=true);
  translate([0,0,L-10])rotate([90, 0,0])cylinder(d=3.5, h=100, $fn=30,center=true);
}



