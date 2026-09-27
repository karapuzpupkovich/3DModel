// Табличка «ОСТОРОЖНО! РАСКОПКИ» — генерируется build_plaques.py
difference() {
  linear_extrude(3.0) union() {
    translate([2.5, 2.5]) offset(r=2.5, $fn=32) square([49.0, 39.0]);
    
  }
  translate([0, 0, 2.2]) linear_extrude(1.8) union() {
    translate([27.0, 32.4375]) offset(r=0.12, $fn=16) text("ОСТОРОЖНО!", font="Shantell Sans:style=ExtraBold", size=4.957, halign="center", valign="baseline", $fn=24);
    translate([27.0, 25.317793812138298]) offset(r=0.12, $fn=16) text("РАСКОПКИ", font="Shantell Sans:style=ExtraBold", size=4.957, halign="center", valign="baseline", $fn=24);
    difference() {
union() {
  hull(){translate([10.387,11.718]) circle(r=0.575,$fn=20);translate([10.840,11.929]) circle(r=0.575,$fn=20);}
  hull(){translate([10.840,11.929]) circle(r=0.575,$fn=20);translate([11.474,12.223]) circle(r=0.575,$fn=20);}
  hull(){translate([11.474,12.223]) circle(r=0.575,$fn=20);translate([12.221,12.572]) circle(r=0.575,$fn=20);}
  hull(){translate([12.221,12.572]) circle(r=0.575,$fn=20);translate([13.015,12.947]) circle(r=0.575,$fn=20);}
  hull(){translate([13.015,12.947]) circle(r=0.575,$fn=20);translate([13.787,13.318]) circle(r=0.575,$fn=20);}
  hull(){translate([13.787,13.318]) circle(r=0.575,$fn=20);translate([14.555,13.700]) circle(r=0.575,$fn=20);}
  hull(){translate([14.555,13.700]) circle(r=0.575,$fn=20);translate([15.363,14.113]) circle(r=0.575,$fn=20);}
  hull(){translate([15.363,14.113]) circle(r=0.575,$fn=20);translate([16.188,14.535]) circle(r=0.575,$fn=20);}
  hull(){translate([16.188,14.535]) circle(r=0.575,$fn=20);translate([17.003,14.943]) circle(r=0.575,$fn=20);}
  hull(){translate([17.003,14.943]) circle(r=0.575,$fn=20);translate([17.787,15.318]) circle(r=0.575,$fn=20);}
  hull(){translate([17.787,15.318]) circle(r=0.575,$fn=20);translate([18.546,15.663]) circle(r=0.575,$fn=20);}
  hull(){translate([18.546,15.663]) circle(r=0.575,$fn=20);translate([19.295,15.992]) circle(r=0.575,$fn=20);}
  hull(){translate([19.295,15.992]) circle(r=0.575,$fn=20);translate([20.024,16.299]) circle(r=0.575,$fn=20);}
  hull(){translate([20.024,16.299]) circle(r=0.575,$fn=20);translate([20.725,16.577]) circle(r=0.575,$fn=20);}
  hull(){translate([20.725,16.577]) circle(r=0.575,$fn=20);translate([21.387,16.818]) circle(r=0.575,$fn=20);}
  hull(){translate([21.387,16.818]) circle(r=0.575,$fn=20);translate([21.989,17.019]) circle(r=0.575,$fn=20);}
  hull(){translate([21.989,17.019]) circle(r=0.575,$fn=20);translate([22.536,17.184]) circle(r=0.575,$fn=20);}
  hull(){translate([22.536,17.184]) circle(r=0.575,$fn=20);translate([23.063,17.319]) circle(r=0.575,$fn=20);}
  hull(){translate([23.063,17.319]) circle(r=0.575,$fn=20);translate([23.602,17.429]) circle(r=0.575,$fn=20);}
  hull(){translate([23.602,17.429]) circle(r=0.575,$fn=20);translate([24.188,17.518]) circle(r=0.575,$fn=20);}
  hull(){translate([24.188,17.518]) circle(r=0.575,$fn=20);translate([24.832,17.586]) circle(r=0.575,$fn=20);}
  hull(){translate([24.832,17.586]) circle(r=0.575,$fn=20);translate([25.514,17.630]) circle(r=0.575,$fn=20);}
  hull(){translate([25.514,17.630]) circle(r=0.575,$fn=20);translate([26.213,17.650]) circle(r=0.575,$fn=20);}
  hull(){translate([26.213,17.650]) circle(r=0.575,$fn=20);translate([26.911,17.646]) circle(r=0.575,$fn=20);}
  hull(){translate([26.911,17.646]) circle(r=0.575,$fn=20);translate([27.587,17.618]) circle(r=0.575,$fn=20);}
  hull(){translate([27.587,17.618]) circle(r=0.575,$fn=20);translate([28.256,17.553]) circle(r=0.575,$fn=20);}
  hull(){translate([28.256,17.553]) circle(r=0.575,$fn=20);translate([28.930,17.451]) circle(r=0.575,$fn=20);}
  hull(){translate([28.930,17.451]) circle(r=0.575,$fn=20);translate([29.589,17.332]) circle(r=0.575,$fn=20);}
  hull(){translate([29.589,17.332]) circle(r=0.575,$fn=20);translate([30.215,17.215]) circle(r=0.575,$fn=20);}
  hull(){translate([30.215,17.215]) circle(r=0.575,$fn=20);translate([30.787,17.118]) circle(r=0.575,$fn=20);}
  hull(){translate([30.787,17.118]) circle(r=0.575,$fn=20);translate([31.301,17.021]) circle(r=0.575,$fn=20);}
  hull(){translate([31.301,17.021]) circle(r=0.575,$fn=20);translate([31.768,16.911]) circle(r=0.575,$fn=20);}
  hull(){translate([31.768,16.911]) circle(r=0.575,$fn=20);translate([32.199,16.820]) circle(r=0.575,$fn=20);}
  hull(){translate([32.199,16.820]) circle(r=0.575,$fn=20);translate([32.602,16.779]) circle(r=0.575,$fn=20);}
  hull(){translate([32.602,16.779]) circle(r=0.575,$fn=20);translate([32.987,16.818]) circle(r=0.575,$fn=20);}
  hull(){translate([32.987,16.818]) circle(r=0.575,$fn=20);translate([33.352,16.960]) circle(r=0.575,$fn=20);}
  hull(){translate([33.352,16.960]) circle(r=0.575,$fn=20);translate([33.690,17.185]) circle(r=0.575,$fn=20);}
  hull(){translate([33.690,17.185]) circle(r=0.575,$fn=20);translate([34.005,17.459]) circle(r=0.575,$fn=20);}
  hull(){translate([34.005,17.459]) circle(r=0.575,$fn=20);translate([34.303,17.747]) circle(r=0.575,$fn=20);}
  hull(){translate([34.303,17.747]) circle(r=0.575,$fn=20);translate([34.587,18.018]) circle(r=0.575,$fn=20);}
  hull(){translate([34.587,18.018]) circle(r=0.575,$fn=20);translate([34.872,18.292]) circle(r=0.575,$fn=20);}
  hull(){translate([34.872,18.292]) circle(r=0.575,$fn=20);translate([35.154,18.593]) circle(r=0.575,$fn=20);}
  hull(){translate([35.154,18.593]) circle(r=0.575,$fn=20);translate([35.413,18.887]) circle(r=0.575,$fn=20);}
  hull(){translate([35.413,18.887]) circle(r=0.575,$fn=20);translate([35.631,19.139]) circle(r=0.575,$fn=20);}
  hull(){translate([35.631,19.139]) circle(r=0.575,$fn=20);translate([35.787,19.318]) circle(r=0.575,$fn=20);}
  hull(){translate([11.877,11.363]) circle(r=0.400,$fn=20);translate([11.074,13.085]) circle(r=0.400,$fn=20);}
  hull(){translate([13.606,12.177]) circle(r=0.400,$fn=20);translate([12.783,13.889]) circle(r=0.400,$fn=20);}
  hull(){translate([15.330,13.029]) circle(r=0.400,$fn=20);translate([14.466,14.721]) circle(r=0.400,$fn=20);}
  hull(){translate([17.017,13.887]) circle(r=0.400,$fn=20);translate([16.166,15.586]) circle(r=0.400,$fn=20);}
  hull(){translate([18.700,14.689]) circle(r=0.400,$fn=20);translate([17.913,16.418]) circle(r=0.400,$fn=20);}
  hull(){translate([25.787,17.318]) circle(r=0.450,$fn=20);translate([26.020,16.314]) circle(r=0.450,$fn=20);}
  hull(){translate([26.020,16.314]) circle(r=0.450,$fn=20);translate([26.155,15.302]) circle(r=0.450,$fn=20);}
  hull(){translate([26.155,15.302]) circle(r=0.450,$fn=20);translate([26.195,14.282]) circle(r=0.450,$fn=20);}
  hull(){translate([26.195,14.282]) circle(r=0.450,$fn=20);translate([26.139,13.254]) circle(r=0.450,$fn=20);}
  hull(){translate([26.139,13.254]) circle(r=0.450,$fn=20);translate([25.987,12.218]) circle(r=0.450,$fn=20);}
  hull(){translate([27.987,17.318]) circle(r=0.450,$fn=20);translate([28.220,16.314]) circle(r=0.450,$fn=20);}
  hull(){translate([28.220,16.314]) circle(r=0.450,$fn=20);translate([28.355,15.302]) circle(r=0.450,$fn=20);}
  hull(){translate([28.355,15.302]) circle(r=0.450,$fn=20);translate([28.395,14.282]) circle(r=0.450,$fn=20);}
  hull(){translate([28.395,14.282]) circle(r=0.450,$fn=20);translate([28.339,13.254]) circle(r=0.450,$fn=20);}
  hull(){translate([28.339,13.254]) circle(r=0.450,$fn=20);translate([28.187,12.218]) circle(r=0.450,$fn=20);}
  hull(){translate([30.188,17.318]) circle(r=0.450,$fn=20);translate([30.420,16.314]) circle(r=0.450,$fn=20);}
  hull(){translate([30.420,16.314]) circle(r=0.450,$fn=20);translate([30.555,15.302]) circle(r=0.450,$fn=20);}
  hull(){translate([30.555,15.302]) circle(r=0.450,$fn=20);translate([30.596,14.282]) circle(r=0.450,$fn=20);}
  hull(){translate([30.596,14.282]) circle(r=0.450,$fn=20);translate([30.540,13.254]) circle(r=0.450,$fn=20);}
  hull(){translate([30.540,13.254]) circle(r=0.450,$fn=20);translate([30.387,12.218]) circle(r=0.450,$fn=20);}
  hull(){translate([32.188,16.718]) circle(r=0.425,$fn=20);translate([32.348,15.966]) circle(r=0.425,$fn=20);}
  hull(){translate([32.348,15.966]) circle(r=0.425,$fn=20);translate([32.428,15.230]) circle(r=0.425,$fn=20);}
  hull(){translate([32.428,15.230]) circle(r=0.425,$fn=20);translate([32.428,14.510]) circle(r=0.425,$fn=20);}
  hull(){translate([32.428,14.510]) circle(r=0.425,$fn=20);translate([32.348,13.806]) circle(r=0.425,$fn=20);}
  hull(){translate([32.348,13.806]) circle(r=0.425,$fn=20);translate([32.188,13.118]) circle(r=0.425,$fn=20);}
  hull(){translate([25.987,12.218]) circle(r=0.400,$fn=20);translate([26.392,12.119]) circle(r=0.400,$fn=20);}
  hull(){translate([26.392,12.119]) circle(r=0.400,$fn=20);translate([26.962,11.963]) circle(r=0.400,$fn=20);}
  hull(){translate([26.962,11.963]) circle(r=0.400,$fn=20);translate([27.629,11.805]) circle(r=0.400,$fn=20);}
  hull(){translate([27.629,11.805]) circle(r=0.400,$fn=20);translate([28.327,11.704]) circle(r=0.400,$fn=20);}
  hull(){translate([28.327,11.704]) circle(r=0.400,$fn=20);translate([28.987,11.718]) circle(r=0.400,$fn=20);}
  hull(){translate([28.987,11.718]) circle(r=0.400,$fn=20);translate([29.666,11.899]) circle(r=0.400,$fn=20);}
  hull(){translate([29.666,11.899]) circle(r=0.400,$fn=20);translate([30.407,12.208]) circle(r=0.400,$fn=20);}
  hull(){translate([30.407,12.208]) circle(r=0.400,$fn=20);translate([31.128,12.567]) circle(r=0.400,$fn=20);}
  hull(){translate([31.128,12.567]) circle(r=0.400,$fn=20);translate([31.749,12.897]) circle(r=0.400,$fn=20);}
  hull(){translate([31.749,12.897]) circle(r=0.400,$fn=20);translate([32.188,13.118]) circle(r=0.400,$fn=20);}
  hull(){translate([33.188,15.418]) circle(r=0.400,$fn=20);translate([34.388,14.118]) circle(r=0.400,$fn=20);}
  hull(){translate([34.388,14.118]) circle(r=0.400,$fn=20);translate([35.388,13.718]) circle(r=0.400,$fn=20);}
  hull(){translate([22.787,16.518]) circle(r=0.600,$fn=20);translate([20.887,12.418]) circle(r=0.600,$fn=20);}
  hull(){translate([20.887,12.418]) circle(r=0.600,$fn=20);translate([22.188,8.718]) circle(r=0.600,$fn=20);}
  hull(){translate([22.188,8.718]) circle(r=0.475,$fn=20);translate([24.387,7.518]) circle(r=0.475,$fn=20);}
  hull(){translate([22.188,8.718]) circle(r=0.425,$fn=20);translate([23.387,7.168]) circle(r=0.425,$fn=20);}
  hull(){translate([23.887,16.418]) circle(r=0.600,$fn=20);translate([25.787,12.618]) circle(r=0.600,$fn=20);}
  hull(){translate([25.787,12.618]) circle(r=0.600,$fn=20);translate([24.587,8.818]) circle(r=0.600,$fn=20);}
  hull(){translate([24.587,8.818]) circle(r=0.475,$fn=20);translate([26.787,7.618]) circle(r=0.475,$fn=20);}
  hull(){translate([24.587,8.818]) circle(r=0.425,$fn=20);translate([25.787,7.268]) circle(r=0.425,$fn=20);}
  polygon([[34.987, 19.018], [35.287, 21.118], [36.888, 22.318], [39.587, 22.718], [42.188, 22.118], [43.887, 21.118], [44.188, 20.118], [41.788, 19.718], [39.587, 19.368], [39.987, 18.018], [43.188, 17.818], [43.487, 17.118], [40.987, 16.718], [37.787, 16.918], [35.888, 17.718]]);
}
union() {
  translate([37.888,20.818]) circle(r=0.650,$fn=40);
  polygon([[39.188, 18.918], [43.987, 19.768], [43.587, 19.068], [42.887, 18.818], [42.188, 18.068], [41.688, 18.768], [40.787, 18.618], [40.188, 17.868], [39.787, 18.518]]);
}
}
  }
}
