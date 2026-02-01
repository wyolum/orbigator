h = 2;

w = 5.3;

module end(){
  difference(){
    union(){
      cylinder(d=w+5, h=h, $fn=30,center=true);
      translate([5, 0, 0])cube([10, 5, h], center=true);
    }
    cylinder(r=w / (2 * cos(30)), h=h+2, $fn=6,center=true);
  }
}

end();
translate([20,0,0])
difference(){
  rotate([0,0,180])end();
  translate([11.5,0,0])cube([20, 20, 20],center=true);
}
