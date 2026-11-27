// Stations, moments and barrier closures for the water replay.
// Made by analysis/water-levels/prepare.py from Rijkswaterstaat data.
export const stations = [
 {
  "key": "vlissingen",
  "name": "Vlissingen",
  "group": "coast",
  "lat": 51.442,
  "lon": 3.6,
  "normal": 14,
  "low": -234,
  "high": 348
 },
 {
  "key": "westkapelle",
  "name": "Westkapelle",
  "group": "coast",
  "lat": 51.5215,
  "lon": 3.44,
  "normal": 12,
  "low": -202,
  "high": 321
 },
 {
  "key": "roompot-buiten",
  "name": "Roompot (sea)",
  "group": "coast",
  "lat": 51.619,
  "lon": 3.68,
  "normal": 12,
  "low": -183,
  "high": 327
 },
 {
  "key": "roompot-binnen",
  "name": "Roompot (Oosterschelde)",
  "group": "behind-barrier",
  "lat": 51.618,
  "lon": 3.688,
  "normal": 23,
  "low": -168,
  "high": 210
 },
 {
  "key": "haringvliet-buiten",
  "name": "Haringvliet (sea)",
  "group": "coast",
  "lat": 51.827,
  "lon": 4.0335,
  "normal": 28,
  "low": -102,
  "high": 323
 },
 {
  "key": "hoek-van-holland",
  "name": "Hoek van Holland",
  "group": "coast",
  "lat": 51.9769,
  "lon": 4.1198,
  "normal": 21,
  "low": -99,
  "high": 313
 },
 {
  "key": "scheveningen",
  "name": "Scheveningen",
  "group": "coast",
  "lat": 52.099,
  "lon": 4.2636,
  "normal": 17,
  "low": -123,
  "high": 305
 },
 {
  "key": "ijmuiden",
  "name": "IJmuiden",
  "group": "coast",
  "lat": 52.463,
  "lon": 4.555,
  "normal": 22,
  "low": -123,
  "high": 291
 },
 {
  "key": "den-helder",
  "name": "Den Helder",
  "group": "coast",
  "lat": 52.9644,
  "lon": 4.745,
  "normal": 46,
  "low": -119,
  "high": 251
 },
 {
  "key": "oudeschild",
  "name": "Texel",
  "group": "coast",
  "lat": 53.0388,
  "lon": 4.8502,
  "normal": 45,
  "low": -124,
  "high": 266
 },
 {
  "key": "den-oever",
  "name": "Den Oever",
  "group": "coast",
  "lat": 52.9315,
  "lon": 5.0456,
  "normal": 50,
  "low": -82,
  "high": 292
 },
 {
  "key": "kornwerderzand",
  "name": "Kornwerderzand Waddenzee buitenhaven",
  "group": "coast",
  "lat": 53.0746,
  "lon": 5.3348,
  "normal": 44,
  "low": -146,
  "high": 317
 },
 {
  "key": "harlingen",
  "name": "Harlingen",
  "group": "coast",
  "lat": 53.1756,
  "lon": 5.4093,
  "normal": 42,
  "low": -151,
  "high": 324
 },
 {
  "key": "vlieland",
  "name": "Vlieland",
  "group": "coast",
  "lat": 53.2961,
  "lon": 5.0915,
  "normal": 31,
  "low": -142,
  "high": 277
 },
 {
  "key": "terschelling",
  "name": "Terschelling",
  "group": "coast",
  "lat": 53.363,
  "lon": 5.22,
  "normal": 37,
  "low": -147,
  "high": 277
 },
 {
  "key": "nes",
  "name": "Ameland",
  "group": "coast",
  "lat": 53.4298,
  "lon": 5.7595,
  "normal": 44,
  "low": -174,
  "high": 319
 },
 {
  "key": "schiermonnikoog",
  "name": "Schiermonnikoog",
  "group": "coast",
  "lat": 53.4689,
  "lon": 6.2029,
  "normal": 47,
  "low": -177,
  "high": 312
 },
 {
  "key": "lauwersoog",
  "name": "Lauwersoog",
  "group": "coast",
  "lat": 53.4083,
  "lon": 6.196,
  "normal": 45,
  "low": -176,
  "high": 322
 },
 {
  "key": "eemshaven",
  "name": "Eemshaven",
  "group": "coast",
  "lat": 53.4487,
  "lon": 6.8284,
  "normal": 46,
  "low": -212,
  "high": 351
 },
 {
  "key": "delfzijl",
  "name": "Delfzijl",
  "group": "coast",
  "lat": 53.328,
  "lon": 6.931,
  "normal": 61,
  "low": -255,
  "high": 412
 },
 {
  "key": "nieuwe-statenzijl",
  "name": "Nieuwe Statenzijl",
  "group": "coast",
  "lat": 53.2316,
  "lon": 7.2074,
  "normal": 75,
  "low": -54,
  "high": 443
 },
 {
  "key": "terneuzen",
  "name": "Terneuzen",
  "group": "scheldt",
  "lat": 51.3362,
  "lon": 3.8198,
  "normal": 28,
  "low": -246,
  "high": 379
 },
 {
  "key": "hansweert",
  "name": "Hansweert",
  "group": "scheldt",
  "lat": 51.4457,
  "lon": 3.9974,
  "normal": 36,
  "low": -254,
  "high": 399
 },
 {
  "key": "bath",
  "name": "Bath",
  "group": "scheldt",
  "lat": 51.3988,
  "lon": 4.2101,
  "normal": 40,
  "low": -271,
  "high": 423
 },
 {
  "key": "maassluis",
  "name": "Maassluis",
  "group": "rotterdam",
  "lat": 51.9175,
  "lon": 4.2498,
  "normal": 31,
  "low": -92,
  "high": 225
 },
 {
  "key": "vlaardingen",
  "name": "Vlaardingen",
  "group": "rotterdam",
  "lat": 51.8996,
  "lon": 4.3491,
  "normal": 36,
  "low": -80,
  "high": 238
 },
 {
  "key": "rotterdam",
  "name": "Rotterdam",
  "group": "rotterdam",
  "lat": 51.8995,
  "lon": 4.5184,
  "normal": 47,
  "low": -48,
  "high": 239
 },
 {
  "key": "spijkenisse",
  "name": "Spijkenisse",
  "group": "rotterdam",
  "lat": 51.8617,
  "lon": 4.3339,
  "normal": 36,
  "low": -70,
  "high": 220
 },
 {
  "key": "krimpen",
  "name": "Krimpen a/d IJssel",
  "group": "rotterdam",
  "lat": 51.9165,
  "lon": 4.579,
  "normal": 51,
  "low": -39,
  "high": 234
 },
 {
  "key": "dordrecht",
  "name": "Dordrecht Oude Maas",
  "group": "rotterdam",
  "lat": 51.82,
  "lon": 4.671,
  "normal": 68,
  "low": 7,
  "high": 197
 },
 {
  "key": "moerdijk",
  "name": "Moerdijk",
  "group": "rotterdam",
  "lat": 51.712,
  "lon": 4.615,
  "normal": 64,
  "low": 9,
  "high": 168
 },
 {
  "key": "goidschalxoord",
  "name": "Heinenoord",
  "group": "rotterdam",
  "lat": 51.8303,
  "lon": 4.4516,
  "normal": 44,
  "low": -35,
  "high": 199
 },
 {
  "key": "lobith",
  "name": "Lobith",
  "group": "rhine",
  "lat": 51.8575,
  "lon": 6.0836,
  "normal": 1304,
  "low": 1198,
  "high": 1432
 },
 {
  "key": "pannerdense-kop",
  "name": "Pannerdense Kop",
  "group": "rhine",
  "lat": 51.872,
  "lon": 6.0417,
  "normal": 1271,
  "low": 1172,
  "high": 1386
 },
 {
  "key": "nijmegen",
  "name": "Nijmegen",
  "group": "rhine",
  "lat": 51.853,
  "lon": 5.854,
  "normal": 1083,
  "low": 986,
  "high": 1182
 },
 {
  "key": "tiel",
  "name": "Tiel Sluis",
  "group": "rhine",
  "lat": 51.899,
  "lon": 5.456,
  "normal": 799,
  "low": 720,
  "high": 887
 },
 {
  "key": "zaltbommel",
  "name": "Zaltbommel",
  "group": "rhine",
  "lat": 51.8152,
  "lon": 5.2447,
  "normal": 515,
  "low": 448,
  "high": 602
 },
 {
  "key": "arnhem",
  "name": "Arnhem",
  "group": "lek",
  "lat": 51.9754,
  "lon": 5.912,
  "normal": 1110,
  "low": 1027,
  "high": 1205
 },
 {
  "key": "driel",
  "name": "Driel",
  "group": "lek",
  "lat": 51.9658,
  "lon": 5.8106,
  "normal": 988,
  "low": 917,
  "high": 1084
 },
 {
  "key": "amerongen",
  "name": "Amerongen",
  "group": "lek",
  "lat": 51.9753,
  "lon": 5.4125,
  "normal": 584,
  "low": 535,
  "high": 682
 },
 {
  "key": "hagestein",
  "name": "Hagestein",
  "group": "lek",
  "lat": 51.9895,
  "lon": 5.1352,
  "normal": 288,
  "low": 249,
  "high": 388
 },
 {
  "key": "schoonhoven",
  "name": "Schoonhoven",
  "group": "lek",
  "lat": 51.942,
  "lon": 4.85,
  "normal": 114,
  "low": 70,
  "high": 245
 },
 {
  "key": "westervoort",
  "name": "Westervoort",
  "group": "ijssel",
  "lat": 51.9705,
  "lon": 5.962,
  "normal": 1122,
  "low": 1051,
  "high": 1211
 },
 {
  "key": "zutphen",
  "name": "Zutphen",
  "group": "ijssel",
  "lat": 52.154,
  "lon": 6.182,
  "normal": 709,
  "low": 708,
  "high": 784
 },
 {
  "key": "deventer",
  "name": "Deventer",
  "group": "ijssel",
  "lat": 52.2512,
  "lon": 6.1532,
  "normal": 554,
  "low": 550,
  "high": 621
 },
 {
  "key": "olst",
  "name": "Olst",
  "group": "ijssel",
  "lat": 52.342,
  "lon": 6.1045,
  "normal": 458,
  "low": 451,
  "high": 530
 },
 {
  "key": "kampen",
  "name": "Kampen",
  "group": "ijssel",
  "lat": 52.552,
  "lon": 5.9264,
  "normal": 41,
  "low": 35,
  "high": 119
 },
 {
  "key": "eijsden",
  "name": "Eijsden",
  "group": "meuse",
  "lat": 50.758,
  "lon": 5.682,
  "normal": 4528,
  "low": 4486,
  "high": 4809
 },
 {
  "key": "maastricht",
  "name": "Sint Pieter Noord",
  "group": "meuse",
  "lat": 50.8303,
  "lon": 5.6973,
  "normal": 4426,
  "low": 4408,
  "high": 4585
 },
 {
  "key": "roermond",
  "name": "Roermond",
  "group": "meuse",
  "lat": 51.2005,
  "lon": 5.9815,
  "normal": 1686,
  "low": 1659,
  "high": 1842
 },
 {
  "key": "venlo",
  "name": "Venlo",
  "group": "meuse",
  "lat": 51.3674,
  "lon": 6.1594,
  "normal": 1221,
  "low": 1217,
  "high": 1582
 },
 {
  "key": "grave",
  "name": "Grave",
  "group": "meuse",
  "lat": 51.761,
  "lon": 5.743,
  "normal": 776,
  "low": 715,
  "high": 857
 },
 {
  "key": "lith",
  "name": "Lith",
  "group": "meuse",
  "lat": 51.81,
  "lon": 5.455,
  "normal": 489,
  "low": 390,
  "high": 505
 },
 {
  "key": "heesbeen",
  "name": "Heesbeen",
  "group": "meuse",
  "lat": 51.7358,
  "lon": 5.1247,
  "normal": 109,
  "low": 88,
  "high": 262
 },
 {
  "key": "keizersveer",
  "name": "Keizersveer",
  "group": "meuse",
  "lat": 51.7191,
  "lon": 4.894,
  "normal": 80,
  "low": 42,
  "high": 182
 }
];
export const moments = [
 {
  "t": "2023-12-21T21:20Z",
  "label": "Storm surge at Hoek van Holland",
  "station": "hoek-van-holland",
  "cm": 313
 },
 {
  "t": "2023-12-28T02:00Z",
  "label": "The Rhine peaks at Lobith",
  "station": "lobith",
  "cm": 1432
 },
 {
  "t": "2024-01-04T03:10Z",
  "label": "The Maas flood wave enters at Eijsden",
  "station": "eijsden",
  "cm": 4809
 }
];
// Spells when the water behind a storm barrier stayed far below the sea,
// so the barrier was shut. Inferred from the levels, not from RWS logs.
export const barriers = [
 {
  "name": "Maeslantkering",
  "from": "2023-12-21T20:20Z",
  "to": "2023-12-22T00:00Z"
 },
 {
  "name": "Oosterscheldekering",
  "from": "2023-12-21T17:40Z",
  "to": "2023-12-21T23:00Z"
 }
];
