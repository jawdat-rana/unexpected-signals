// Stations, moments and barrier closures for the water replay.
// Made by analysis/water-levels/prepare.py from Rijkswaterstaat data.
export const stations = [
 {
  "key": "vlissingen",
  "name": "Vlissingen",
  "group": "coast",
  "lat": 51.44,
  "lon": 3.6,
  "normal": 10,
  "low": -100,
  "high": 350
 },
 {
  "key": "hoek-van-holland",
  "name": "Hoek van Holland",
  "group": "coast",
  "lat": 51.98,
  "lon": 4.12,
  "normal": 8,
  "low": -100,
  "high": 347
 },
 {
  "key": "den-helder",
  "name": "Den Helder",
  "group": "coast",
  "lat": 52.96,
  "lon": 4.75,
  "normal": 5,
  "low": -100,
  "high": 304
 },
 {
  "key": "delfzijl",
  "name": "Delfzijl",
  "group": "coast",
  "lat": 53.33,
  "lon": 6.93,
  "normal": 4,
  "low": -100,
  "high": 297
 },
 {
  "key": "maassluis",
  "name": "Maassluis",
  "group": "rotterdam",
  "lat": 51.92,
  "lon": 4.25,
  "normal": 8,
  "low": -100,
  "high": 142
 },
 {
  "key": "rotterdam",
  "name": "Rotterdam",
  "group": "rotterdam",
  "lat": 51.91,
  "lon": 4.49,
  "normal": 7,
  "low": -100,
  "high": 157
 },
 {
  "key": "lobith",
  "name": "Lobith",
  "group": "rhine",
  "lat": 51.86,
  "lon": 6.11,
  "normal": 1033,
  "low": 1000,
  "high": 1500
 },
 {
  "key": "venlo",
  "name": "Venlo",
  "group": "meuse",
  "lat": 51.37,
  "lon": 6.17,
  "normal": 1033,
  "low": 1000,
  "high": 1500
 },
 {
  "key": "roompot-buiten",
  "name": "Roompot (sea)",
  "group": "coast",
  "lat": 51.62,
  "lon": 3.68,
  "normal": 10,
  "low": -100,
  "high": 350
 },
 {
  "key": "roompot-binnen",
  "name": "Roompot (Oosterschelde)",
  "group": "behind-barrier",
  "lat": 51.64,
  "lon": 3.75,
  "normal": 9,
  "low": -100,
  "high": 131
 }
];
export const moments = [
 {
  "t": "2023-12-21T18:50Z",
  "label": "Storm surge at Hoek van Holland",
  "station": "hoek-van-holland",
  "cm": 347
 },
 {
  "t": "2023-12-26T10:30Z",
  "label": "The Rhine peaks at Lobith",
  "station": "lobith",
  "cm": 1500
 },
 {
  "t": "2023-12-26T10:30Z",
  "label": "The Maas peaks at Venlo",
  "station": "venlo",
  "cm": 1500
 }
];
// Spells when the water behind a storm barrier stayed far below the sea,
// so the barrier was shut. Inferred from the levels, not from RWS logs.
export const barriers = [
 {
  "name": "Maeslantkering",
  "from": "2023-12-21T14:00Z",
  "to": "2023-12-21T22:50Z"
 },
 {
  "name": "Oosterscheldekering",
  "from": "2023-12-21T14:10Z",
  "to": "2023-12-21T22:20Z"
 }
];
