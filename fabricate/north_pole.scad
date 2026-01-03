$fn=50;

globe_d = 299;
globe_r = globe_d/2;

offset = 4;

module clip(){
  difference(){
    union(){
      cylinder(d1=9, d2=11, h=1.5);
      translate([0,0,1.4])cylinder(d=9.5, h=3.4);
    }
    for(theta=[0, 90]){
      rotate([0,0,theta])cube([20, 2, 8],center=true);
    }
    translate([0,0,-1])
      cylinder(d=6, h=10);
  }
}
difference(){
  translate([0, 0, globe_r-1])
  union(){
    {
      cylinder(d=25, h=1);
      translate([0,0,1])cylinder(d1=25, d2=2, h=2);
    }
  }
  sphere(d=299, $fn=300);
}

rotate([atan(4/globe_r), 0, 0])translate([0,0,globe_r-4])clip();
