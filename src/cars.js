// Car definitions. Units: metres, m/s. Shape: z runs rear(-)->front(+), y up.
// body*: side profile of the lower body, cabin: glass greenhouse.
export const MPH = 2.23694;

export const CARS = {
  fiat126: {
    id: 'fiat126', name: 'FIAT 126P "MALUCH"', origin: 'Poland',
    color: '#c8321f', vmax: 31, t60: 22, grip: 0.85, steer: 0.5,
    L: 3.05, W: 1.38, wheelR: 0.27, wb: 1.84, gc: 0.2,
    noseY: 0.62, hoodY: 0.78, tailY: 0.9, beltY: 0.88,
    cabin: { z0: 0.55, z1: 0.35, z2: -0.95, z3: -1.25, roofY: 1.42 },
    spoiler: false, rearEngine: true,
  },
  corsa: {
    id: 'corsa', name: 'OPEL CORSA', origin: 'Germany',
    color: '#d9d9d9', vmax: 52, t60: 11, grip: 0.95, steer: 0.5,
    L: 3.73, W: 1.6, wheelR: 0.29, wb: 2.39, gc: 0.16,
    noseY: 0.6, hoodY: 0.82, tailY: 0.95, beltY: 0.94,
    cabin: { z0: 0.6, z1: 0.15, z2: -1.15, z3: -1.75, roofY: 1.42 },
    spoiler: false,
  },
  impreza: {
    id: 'impreza', name: 'SUBARU IMPREZA 22B', origin: 'Japan',
    color: '#1b3a9c', vmax: 68, t60: 5.3, grip: 1.15, steer: 0.5,
    L: 4.34, W: 1.75, wheelR: 0.32, wb: 2.52, gc: 0.14,
    noseY: 0.56, hoodY: 0.8, tailY: 0.98, beltY: 0.98,
    cabin: { z0: 0.55, z1: -0.2, z2: -1.2, z3: -1.85, roofY: 1.38 },
    spoiler: true, wheelColor: '#d4a63a',
  },
  gtr: {
    id: 'gtr', name: 'NISSAN SKYLINE GT-R', origin: 'Japan',
    color: '#8da1b9', vmax: 82, t60: 4.5, grip: 1.25, steer: 0.5,
    L: 4.6, W: 1.79, wheelR: 0.33, wb: 2.67, gc: 0.12,
    noseY: 0.5, hoodY: 0.78, tailY: 0.97, beltY: 0.96,
    cabin: { z0: 0.6, z1: -0.15, z2: -1.25, z3: -1.9, roofY: 1.34 },
    spoiler: true,
  },
  f40: {
    id: 'f40', name: 'FERRARI F40', origin: 'Italy',
    color: '#d2111a', vmax: 90, t60: 4.1, grip: 1.2, steer: 0.5,
    L: 4.36, W: 1.97, wheelR: 0.33, wb: 2.45, gc: 0.1,
    noseY: 0.4, hoodY: 0.62, tailY: 0.98, beltY: 0.82,
    cabin: { z0: 0.25, z1: -0.4, z2: -1.3, z3: -1.7, roofY: 1.13 },
    spoiler: true, bigWing: true,
  },
  lambo: {
    id: 'lambo', name: 'LAMBORGHINI "SAKURA DRIFT"', origin: 'Italy / Japan',
    color: '#ff4fa3', vmax: 98, t60: 3.3, grip: 1.3, steer: 0.5,
    L: 4.55, W: 2.03, wheelR: 0.34, wb: 2.7, gc: 0.1,
    noseY: 0.38, hoodY: 0.58, tailY: 0.95, beltY: 0.8,
    cabin: { z0: 0.55, z1: -0.1, z2: -1.2, z3: -1.85, roofY: 1.1 },
    spoiler: true, bigWing: true, wheelColor: '#31e0ff', livery: true,
  },
};


// ---- non-player vehicles: civilian traffic + police
export const NPC_CARS = {
  octavia: {
    id: 'octavia', name: 'SKODA OCTAVIA', color: '#8d98a6', vmax: 58, t60: 9, grip: 1.0, steer: 0.5, mass: 1300,
    L: 4.65, W: 1.8, wheelR: 0.31, wb: 2.68, gc: 0.15,
    noseY: 0.6, hoodY: 0.86, tailY: 1.0, beltY: 1.0,
    cabin: { z0: 0.75, z1: 0.1, z2: -1.2, z3: -1.75, roofY: 1.45 },
  },
  van: {
    id: 'van', name: 'TRANSIT VAN', color: '#e9e9e9', vmax: 45, t60: 14, grip: 0.85, steer: 0.45, mass: 2200,
    L: 5.0, W: 1.95, wheelR: 0.33, wb: 3.0, gc: 0.2,
    noseY: 0.85, hoodY: 1.0, tailY: 1.25, beltY: 1.2,
    cabin: { z0: 1.3, z1: 1.05, z2: -2.3, z3: -2.4, roofY: 2.25 },
  },
  blackcab: {
    id: 'blackcab', name: 'BLACK CAB', color: '#0d0d10', vmax: 40, t60: 14, grip: 0.9, steer: 0.5, mass: 1900,
    L: 4.6, W: 1.8, wheelR: 0.33, wb: 2.8, gc: 0.17,
    noseY: 0.65, hoodY: 0.9, tailY: 1.2, beltY: 1.1,
    cabin: { z0: 0.9, z1: 0.55, z2: -1.9, z3: -2.2, roofY: 1.75 },
  },
  bus: {
    id: 'bus', name: 'LONDON BUS', color: '#d4231e', vmax: 24, t60: 28, grip: 0.8, steer: 0.4, mass: 11000, bus: true,
    L: 11.2, W: 2.5, wheelR: 0.5, wb: 5.8, gc: 0.35,
    noseY: 1.3, hoodY: 1.4, tailY: 1.5, beltY: 1.5,
    cabin: { z0: 5.4, z1: 5.3, z2: -5.4, z3: -5.5, roofY: 4.3 },
  },
  cruiser: {
    id: 'cruiser', name: 'POLICE CRUISER', color: '#f2f2f2', vmax: 56, t60: 9, grip: 1.05, steer: 0.5, mass: 1500, police: true,
    L: 4.65, W: 1.8, wheelR: 0.31, wb: 2.68, gc: 0.15,
    noseY: 0.6, hoodY: 0.86, tailY: 1.0, beltY: 1.0,
    cabin: { z0: 0.75, z1: 0.1, z2: -1.2, z3: -1.75, roofY: 1.45 },
  },
  interceptor: {
    id: 'interceptor', name: 'POLICE INTERCEPTOR', color: '#f4f4f4', vmax: 78, t60: 4.8, grip: 1.2, steer: 0.5, mass: 1700, police: true,
    L: 4.85, W: 1.88, wheelR: 0.34, wb: 2.85, gc: 0.13,
    noseY: 0.55, hoodY: 0.82, tailY: 1.0, beltY: 0.98,
    cabin: { z0: 0.7, z1: 0.0, z2: -1.25, z3: -1.9, roofY: 1.4 }, spoiler: true,
  },
  suv: {
    id: 'suv', name: 'POLICE RESPONSE SUV', color: '#15171c', vmax: 66, t60: 7, grip: 1.05, steer: 0.45, mass: 2700, police: true,
    L: 4.95, W: 2.0, wheelR: 0.4, wb: 2.9, gc: 0.25,
    noseY: 1.0, hoodY: 1.2, tailY: 1.5, beltY: 1.35,
    cabin: { z0: 0.9, z1: 0.6, z2: -2.0, z3: -2.45, roofY: 1.9 },
  },
};

// Kenney-model civilians (CC0). def.kenney = glb file, scaled to def.L metres.
const K = (id, kenney, name, L, W, wb, vmax, t60, mass) => ({ id, kenney, name, color: '#9aa0aa', vmax, t60, grip: 1.0, steer: 0.5, mass, L, W, wheelR: 0.33, wb, gc: 0.15 });
Object.assign(NPC_CARS, {
  k_sedan: K('k_sedan', 'sedan', 'SEDAN', 4.6, 1.8, 2.7, 56, 9, 1300),
  k_hatch: K('k_hatch', 'hatchback-sports', 'HATCHBACK', 3.9, 1.7, 2.45, 52, 9, 1050),
  k_sporty: K('k_sporty', 'sedan-sports', 'SPORTS SALOON', 4.5, 1.8, 2.65, 66, 6.5, 1300),
  k_suv: K('k_suv', 'suv', 'SUV', 4.8, 1.95, 2.85, 52, 10, 2000),
  k_suvlux: K('k_suvlux', 'suv-luxury', 'LUXURY SUV', 4.9, 2.0, 2.9, 58, 8, 2300),
  k_van: K('k_van', 'van', 'VAN', 5.2, 2.0, 3.1, 44, 14, 2200),
  k_delivery: K('k_delivery', 'delivery', 'DELIVERY TRUCK', 6.6, 2.2, 3.9, 40, 18, 4500),
});
export const MASS = { fiat126: 700, corsa: 950, impreza: 1250, gtr: 1600, f40: 1100, lambo: 1500 };
export const defOf = id => CARS[id] || NPC_CARS[id];

export const CAR_ORDER = ['fiat126', 'corsa', 'impreza', 'gtr', 'f40', 'lambo'];
