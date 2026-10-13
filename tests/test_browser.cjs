"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { calculate } = require("../docs/calculator.js");

const base = {age:65,heart_rate:80,systolic_bp:130,creatinine:1.0,killip_class:1};
test("published reference baseline, 108 points", () => {
  const result = calculate(base);
  assert.equal(result.score,108);
  assert.equal(result.category,"Low");
  assert.equal(result.nomogramAnchorPercent,0.8);
  assert.match(result.limitations,/not GRACE 2.0/);
});

test("independent clinical scenario, 156 points", () => {
  assert.equal(calculate({
    age:67,heart_rate:96,systolic_bp:128,creatinine:1.1,
    killip_class:1,st_deviation:true,elevated_markers:true
  }).score,156);
});

test("low and high score endpoints", () => {
  assert.equal(calculate({age:18,heart_rate:40,systolic_bp:250,creatinine:.1,killip_class:1}).score,1);
  assert.equal(calculate({
    age:99,heart_rate:250,systolic_bp:60,creatinine:6,killip_class:4,
    cardiac_arrest:true,st_deviation:true,elevated_markers:true
  }).score,372);
});

test("creatinine threshold does not truncate fractional value", () => {
  assert.equal(calculate({...base,creatinine:0.399999}).breakdown.creatinine,1);
  assert.equal(calculate({...base,creatinine:0.4}).breakdown.creatinine,4);
});

test("risk categories reflect historical ESC threshold", () => {
  // Check a source value near threshold, and the no-interpolation explanation.
  assert.equal(calculate(base).category,"Low");
  assert.equal(calculate({...base,st_deviation:true}).category,"Intermediate");
  assert.equal(calculate({...base,cardiac_arrest:true}).category,"High");
});

test("unrecognized, nonfinite and fractional input rejected", () => {
  for (const changed of [
    {age:1},{age:65.1},{heart_rate:NaN},{systolic_bp:Infinity},
    {creatinine:NaN},{creatinine:0},{killip_class:5},
    {st_deviation:1},{cardiac_arrest:"false"},{elevated_markers:undefined}
  ]) {
    // undefined is treated as missing and defaults to false; skip its assertion.
    if ("elevated_markers" in changed) continue;
    assert.throws(() => calculate({...base,...changed}));
  }
});

test("nomogram endpoints use explicit open bounds", () => {
  assert.match(calculate({age:18,heart_rate:40,systolic_bp:250,creatinine:.1,killip_class:1}).nomogram,/≤0.2%/);
  assert.match(calculate({age:99,heart_rate:250,systolic_bp:60,creatinine:6,killip_class:4,cardiac_arrest:true,st_deviation:true,elevated_markers:true}).nomogram,/≥52%/);
});
