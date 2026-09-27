// Табличка «ОСТОРОЖНО! РАСКОПКИ» — генерируется build_plaques.py
difference() {
  linear_extrude(3.0) union() {
    translate([2.5, 42.5]) offset(r=2.5, $fn=32) square([49.0, 39.0]);
    translate([24.0, 7]) square([6.0, 36.0]);
    hull() { translate([24.0, 7]) square([6.0, 0.01]); translate([27.0, 1.1]) circle(r=0.9, $fn=24); }
  }
  translate([0, 0, 2.2]) linear_extrude(1.8) union() {
    translate([27.0, 72.4375]) offset(r=0.12, $fn=16) text("ОСТОРОЖНО!", font="Shantell Sans:style=ExtraBold", size=4.957, halign="center", valign="baseline", $fn=24);
    translate([27.0, 65.3177938121383]) offset(r=0.12, $fn=16) text("РАСКОПКИ", font="Shantell Sans:style=ExtraBold", size=4.957, halign="center", valign="baseline", $fn=24);
    difference() {
union() {
  hull(){translate([10.387,51.718]) circle(r=0.575,$fn=20);translate([10.840,51.929]) circle(r=0.575,$fn=20);}
  hull(){translate([10.840,51.929]) circle(r=0.575,$fn=20);translate([11.474,52.223]) circle(r=0.575,$fn=20);}
  hull(){translate([11.474,52.223]) circle(r=0.575,$fn=20);translate([12.221,52.572]) circle(r=0.575,$fn=20);}
  hull(){translate([12.221,52.572]) circle(r=0.575,$fn=20);translate([13.015,52.947]) circle(r=0.575,$fn=20);}
  hull(){translate([13.015,52.947]) circle(r=0.575,$fn=20);translate([13.787,53.318]) circle(r=0.575,$fn=20);}
  hull(){translate([13.787,53.318]) circle(r=0.575,$fn=20);translate([14.555,53.700]) circle(r=0.575,$fn=20);}
  hull(){translate([14.555,53.700]) circle(r=0.575,$fn=20);translate([15.363,54.113]) circle(r=0.575,$fn=20);}
  hull(){translate([15.363,54.113]) circle(r=0.575,$fn=20);translate([16.188,54.535]) circle(r=0.575,$fn=20);}
  hull(){translate([16.188,54.535]) circle(r=0.575,$fn=20);translate([17.003,54.943]) circle(r=0.575,$fn=20);}
  hull(){translate([17.003,54.943]) circle(r=0.575,$fn=20);translate([17.787,55.318]) circle(r=0.575,$fn=20);}
  hull(){translate([17.787,55.318]) circle(r=0.575,$fn=20);translate([18.546,55.663]) circle(r=0.575,$fn=20);}
  hull(){translate([18.546,55.663]) circle(r=0.575,$fn=20);translate([19.295,55.992]) circle(r=0.575,$fn=20);}
  hull(){translate([19.295,55.992]) circle(r=0.575,$fn=20);translate([20.024,56.299]) circle(r=0.575,$fn=20);}
  hull(){translate([20.024,56.299]) circle(r=0.575,$fn=20);translate([20.725,56.577]) circle(r=0.575,$fn=20);}
  hull(){translate([20.725,56.577]) circle(r=0.575,$fn=20);translate([21.387,56.818]) circle(r=0.575,$fn=20);}
  hull(){translate([21.387,56.818]) circle(r=0.575,$fn=20);translate([21.989,57.019]) circle(r=0.575,$fn=20);}
  hull(){translate([21.989,57.019]) circle(r=0.575,$fn=20);translate([22.536,57.184]) circle(r=0.575,$fn=20);}
  hull(){translate([22.536,57.184]) circle(r=0.575,$fn=20);translate([23.063,57.319]) circle(r=0.575,$fn=20);}
  hull(){translate([23.063,57.319]) circle(r=0.575,$fn=20);translate([23.602,57.429]) circle(r=0.575,$fn=20);}
  hull(){translate([23.602,57.429]) circle(r=0.575,$fn=20);translate([24.188,57.518]) circle(r=0.575,$fn=20);}
  hull(){translate([24.188,57.518]) circle(r=0.575,$fn=20);translate([24.832,57.586]) circle(r=0.575,$fn=20);}
  hull(){translate([24.832,57.586]) circle(r=0.575,$fn=20);translate([25.514,57.630]) circle(r=0.575,$fn=20);}
  hull(){translate([25.514,57.630]) circle(r=0.575,$fn=20);translate([26.213,57.650]) circle(r=0.575,$fn=20);}
  hull(){translate([26.213,57.650]) circle(r=0.575,$fn=20);translate([26.911,57.646]) circle(r=0.575,$fn=20);}
  hull(){translate([26.911,57.646]) circle(r=0.575,$fn=20);translate([27.587,57.618]) circle(r=0.575,$fn=20);}
  hull(){translate([27.587,57.618]) circle(r=0.575,$fn=20);translate([28.256,57.553]) circle(r=0.575,$fn=20);}
  hull(){translate([28.256,57.553]) circle(r=0.575,$fn=20);translate([28.930,57.451]) circle(r=0.575,$fn=20);}
  hull(){translate([28.930,57.451]) circle(r=0.575,$fn=20);translate([29.589,57.332]) circle(r=0.575,$fn=20);}
  hull(){translate([29.589,57.332]) circle(r=0.575,$fn=20);translate([30.215,57.215]) circle(r=0.575,$fn=20);}
  hull(){translate([30.215,57.215]) circle(r=0.575,$fn=20);translate([30.787,57.118]) circle(r=0.575,$fn=20);}
  hull(){translate([30.787,57.118]) circle(r=0.575,$fn=20);translate([31.301,57.021]) circle(r=0.575,$fn=20);}
  hull(){translate([31.301,57.021]) circle(r=0.575,$fn=20);translate([31.768,56.911]) circle(r=0.575,$fn=20);}
  hull(){translate([31.768,56.911]) circle(r=0.575,$fn=20);translate([32.199,56.820]) circle(r=0.575,$fn=20);}
  hull(){translate([32.199,56.820]) circle(r=0.575,$fn=20);translate([32.602,56.779]) circle(r=0.575,$fn=20);}
  hull(){translate([32.602,56.779]) circle(r=0.575,$fn=20);translate([32.987,56.818]) circle(r=0.575,$fn=20);}
  hull(){translate([32.987,56.818]) circle(r=0.575,$fn=20);translate([33.352,56.960]) circle(r=0.575,$fn=20);}
  hull(){translate([33.352,56.960]) circle(r=0.575,$fn=20);translate([33.690,57.185]) circle(r=0.575,$fn=20);}
  hull(){translate([33.690,57.185]) circle(r=0.575,$fn=20);translate([34.005,57.459]) circle(r=0.575,$fn=20);}
  hull(){translate([34.005,57.459]) circle(r=0.575,$fn=20);translate([34.303,57.747]) circle(r=0.575,$fn=20);}
  hull(){translate([34.303,57.747]) circle(r=0.575,$fn=20);translate([34.587,58.018]) circle(r=0.575,$fn=20);}
  hull(){translate([34.587,58.018]) circle(r=0.575,$fn=20);translate([34.872,58.292]) circle(r=0.575,$fn=20);}
  hull(){translate([34.872,58.292]) circle(r=0.575,$fn=20);translate([35.154,58.593]) circle(r=0.575,$fn=20);}
  hull(){translate([35.154,58.593]) circle(r=0.575,$fn=20);translate([35.413,58.887]) circle(r=0.575,$fn=20);}
  hull(){translate([35.413,58.887]) circle(r=0.575,$fn=20);translate([35.631,59.139]) circle(r=0.575,$fn=20);}
  hull(){translate([35.631,59.139]) circle(r=0.575,$fn=20);translate([35.787,59.318]) circle(r=0.575,$fn=20);}
  hull(){translate([11.877,51.363]) circle(r=0.400,$fn=20);translate([11.074,53.085]) circle(r=0.400,$fn=20);}
  hull(){translate([13.606,52.177]) circle(r=0.400,$fn=20);translate([12.783,53.889]) circle(r=0.400,$fn=20);}
  hull(){translate([15.330,53.029]) circle(r=0.400,$fn=20);translate([14.466,54.721]) circle(r=0.400,$fn=20);}
  hull(){translate([17.017,53.887]) circle(r=0.400,$fn=20);translate([16.166,55.586]) circle(r=0.400,$fn=20);}
  hull(){translate([18.700,54.689]) circle(r=0.400,$fn=20);translate([17.913,56.418]) circle(r=0.400,$fn=20);}
  hull(){translate([25.787,57.318]) circle(r=0.450,$fn=20);translate([26.020,56.314]) circle(r=0.450,$fn=20);}
  hull(){translate([26.020,56.314]) circle(r=0.450,$fn=20);translate([26.155,55.302]) circle(r=0.450,$fn=20);}
  hull(){translate([26.155,55.302]) circle(r=0.450,$fn=20);translate([26.195,54.282]) circle(r=0.450,$fn=20);}
  hull(){translate([26.195,54.282]) circle(r=0.450,$fn=20);translate([26.139,53.254]) circle(r=0.450,$fn=20);}
  hull(){translate([26.139,53.254]) circle(r=0.450,$fn=20);translate([25.987,52.218]) circle(r=0.450,$fn=20);}
  hull(){translate([27.987,57.318]) circle(r=0.450,$fn=20);translate([28.220,56.314]) circle(r=0.450,$fn=20);}
  hull(){translate([28.220,56.314]) circle(r=0.450,$fn=20);translate([28.355,55.302]) circle(r=0.450,$fn=20);}
  hull(){translate([28.355,55.302]) circle(r=0.450,$fn=20);translate([28.395,54.282]) circle(r=0.450,$fn=20);}
  hull(){translate([28.395,54.282]) circle(r=0.450,$fn=20);translate([28.339,53.254]) circle(r=0.450,$fn=20);}
  hull(){translate([28.339,53.254]) circle(r=0.450,$fn=20);translate([28.187,52.218]) circle(r=0.450,$fn=20);}
  hull(){translate([30.188,57.318]) circle(r=0.450,$fn=20);translate([30.420,56.314]) circle(r=0.450,$fn=20);}
  hull(){translate([30.420,56.314]) circle(r=0.450,$fn=20);translate([30.555,55.302]) circle(r=0.450,$fn=20);}
  hull(){translate([30.555,55.302]) circle(r=0.450,$fn=20);translate([30.596,54.282]) circle(r=0.450,$fn=20);}
  hull(){translate([30.596,54.282]) circle(r=0.450,$fn=20);translate([30.540,53.254]) circle(r=0.450,$fn=20);}
  hull(){translate([30.540,53.254]) circle(r=0.450,$fn=20);translate([30.387,52.218]) circle(r=0.450,$fn=20);}
  hull(){translate([32.188,56.718]) circle(r=0.425,$fn=20);translate([32.348,55.966]) circle(r=0.425,$fn=20);}
  hull(){translate([32.348,55.966]) circle(r=0.425,$fn=20);translate([32.428,55.230]) circle(r=0.425,$fn=20);}
  hull(){translate([32.428,55.230]) circle(r=0.425,$fn=20);translate([32.428,54.510]) circle(r=0.425,$fn=20);}
  hull(){translate([32.428,54.510]) circle(r=0.425,$fn=20);translate([32.348,53.806]) circle(r=0.425,$fn=20);}
  hull(){translate([32.348,53.806]) circle(r=0.425,$fn=20);translate([32.188,53.118]) circle(r=0.425,$fn=20);}
  hull(){translate([25.987,52.218]) circle(r=0.400,$fn=20);translate([26.392,52.119]) circle(r=0.400,$fn=20);}
  hull(){translate([26.392,52.119]) circle(r=0.400,$fn=20);translate([26.962,51.963]) circle(r=0.400,$fn=20);}
  hull(){translate([26.962,51.963]) circle(r=0.400,$fn=20);translate([27.629,51.805]) circle(r=0.400,$fn=20);}
  hull(){translate([27.629,51.805]) circle(r=0.400,$fn=20);translate([28.327,51.704]) circle(r=0.400,$fn=20);}
  hull(){translate([28.327,51.704]) circle(r=0.400,$fn=20);translate([28.987,51.718]) circle(r=0.400,$fn=20);}
  hull(){translate([28.987,51.718]) circle(r=0.400,$fn=20);translate([29.666,51.899]) circle(r=0.400,$fn=20);}
  hull(){translate([29.666,51.899]) circle(r=0.400,$fn=20);translate([30.407,52.208]) circle(r=0.400,$fn=20);}
  hull(){translate([30.407,52.208]) circle(r=0.400,$fn=20);translate([31.128,52.567]) circle(r=0.400,$fn=20);}
  hull(){translate([31.128,52.567]) circle(r=0.400,$fn=20);translate([31.749,52.897]) circle(r=0.400,$fn=20);}
  hull(){translate([31.749,52.897]) circle(r=0.400,$fn=20);translate([32.188,53.118]) circle(r=0.400,$fn=20);}
  hull(){translate([33.188,55.418]) circle(r=0.400,$fn=20);translate([34.388,54.118]) circle(r=0.400,$fn=20);}
  hull(){translate([34.388,54.118]) circle(r=0.400,$fn=20);translate([35.388,53.718]) circle(r=0.400,$fn=20);}
  hull(){translate([22.787,56.518]) circle(r=0.600,$fn=20);translate([20.887,52.418]) circle(r=0.600,$fn=20);}
  hull(){translate([20.887,52.418]) circle(r=0.600,$fn=20);translate([22.188,48.718]) circle(r=0.600,$fn=20);}
  hull(){translate([22.188,48.718]) circle(r=0.475,$fn=20);translate([24.387,47.518]) circle(r=0.475,$fn=20);}
  hull(){translate([22.188,48.718]) circle(r=0.425,$fn=20);translate([23.387,47.168]) circle(r=0.425,$fn=20);}
  hull(){translate([23.887,56.418]) circle(r=0.600,$fn=20);translate([25.787,52.618]) circle(r=0.600,$fn=20);}
  hull(){translate([25.787,52.618]) circle(r=0.600,$fn=20);translate([24.587,48.818]) circle(r=0.600,$fn=20);}
  hull(){translate([24.587,48.818]) circle(r=0.475,$fn=20);translate([26.787,47.618]) circle(r=0.475,$fn=20);}
  hull(){translate([24.587,48.818]) circle(r=0.425,$fn=20);translate([25.787,47.268]) circle(r=0.425,$fn=20);}
  polygon([[34.987, 59.018], [35.287, 61.118], [36.888, 62.318], [39.587, 62.718], [42.188, 62.118], [43.887, 61.118], [44.188, 60.118], [41.788, 59.718], [39.587, 59.368], [39.987, 58.018], [43.188, 57.818], [43.487, 57.118], [40.987, 56.718], [37.787, 56.918], [35.888, 57.718]]);
}
union() {
  translate([37.888,60.818]) circle(r=0.650,$fn=40);
  polygon([[39.188, 58.918], [43.987, 59.768], [43.587, 59.068], [42.887, 58.818], [42.188, 58.068], [41.688, 58.768], [40.787, 58.618], [40.188, 57.868], [39.787, 58.518]]);
}
}
  }
}
