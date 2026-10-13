/* Historical 2003 GRACE in-hospital score. DOI:10.1001/archinte.163.19.2345 */
(function (root, factory) {
  "use strict";
  const calculator = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = calculator;
  if (root) root.GRACE = calculator;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const age = [[30,8],[40,25],[50,41],[60,58],[70,75],[80,91],[90,100]];
  const hr = [[50,3],[70,9],[90,15],[110,24],[150,38],[200,46]];
  const cr = [[0,1],[0.4,4],[0.8,7],[1.2,10],[1.6,13],[2,21],[4,28]];
  const killip = [0,0,20,39,59];
  const nomogram = [[60,0.2],[70,0.3],[80,0.4],[90,0.6],[100,0.8],[110,1.1],[120,1.6],[130,2.1],[140,2.9],[150,3.9],[160,5.4],[170,7.3],[180,9.8],[190,13],[200,18],[210,23],[220,29],[230,36],[240,44],[250,52]];
  function lookup(value, table) {
    let pts = 0;
    for (const [threshold, points] of table) {
      if (value >= threshold) pts = points; else break;
    }
    return pts;
  }
  function integer(label, value, min, max) {
    if (typeof value !== "number" || !Number.isInteger(value) || value < min || value > max) {
      throw new RangeError(label + " must be a whole number between " + min + " and " + max);
    }
  }
  function calculate(input) {
    if (!input || typeof input !== "object") throw new TypeError("Clinical parameters required");
    const { age: a, heart_rate: h, systolic_bp: bp, creatinine: c, killip_class: k,
      cardiac_arrest: arrest = false, st_deviation: st = false, elevated_markers: markers = false } = input;
    integer("Age", a, 18, 120);
    integer("Heart rate", h, 20, 300);
    integer("Systolic BP", bp, 50, 300);
    integer("Killip class", k, 1, 4);
    if (typeof c !== "number" || !Number.isFinite(c) || c < 0.1 || c > 20) {
      throw new RangeError("Creatinine must be between 0.1 and 20 mg/dL");
    }
    for (const [name, flag] of [["Cardiac arrest", arrest],["ST deviation", st],["Elevated markers", markers]]) {
      if (typeof flag !== "boolean") throw new TypeError(name + " must be true or false");
    }
    const breakdown = {
      age: lookup(a, age),
      heartRate: lookup(h, hr),
      systolicBP: bp < 80 ? 58 : bp < 100 ? 53 : bp < 120 ? 43 : bp < 140 ? 34 : bp < 160 ? 24 : bp < 200 ? 10 : 0,
      creatinine: lookup(c, cr),
      killip: killip[k],
      cardiacArrest: arrest ? 39 : 0,
      stDeviation: st ? 28 : 0,
      markers: markers ? 14 : 0
    };
    const score = Object.values(breakdown).reduce((total, points) => total + points, 0);
    const category = score <= 108 ? "Low" : score <= 140 ? "Intermediate" : "High";
    const historicalBand = score <= 108 ? "<1%" : score <= 140 ? "1–3%" : ">3%";
    let label, percent;
    if (score <= 60) {
      label = "≤0.2% (published ≤60 anchor)"; percent = 0.2;
    } else if (score >= 250) {
      label = "≥52% (published ≥250 anchor)"; percent = 52;
    } else {
      const anchor = nomogram.filter(([point]) => point <= score).at(-1);
      percent = anchor[1];
      label = percent + "% (score-" + anchor[0] + " nomogram anchor; not interpolated)";
    }
    return { score, category, historicalBand, nomogram: label, nomogramAnchorPercent: percent, breakdown,
      model: "Original GRACE 2003 in-hospital nomogram",
      limitations: "Historical anchored estimate only; not GRACE 2.0. Six-month risk is not calculated." };
  }
  return Object.freeze({ calculate });
});
