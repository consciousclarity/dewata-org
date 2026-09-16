"use strict";

// Executes the pinned Peradnya library itself. Dates are constructed in UTC;
// run.py also forces TZ=UTC because date-fns 1.x uses local calendar dates.
const fs = require("fs");
const path = require("path");

const root = process.argv[2];
if (!root) {
  throw new Error("usage: node peradnya_adapter.js PERADNYA_ROOT");
}
const { BalineseDate } = require(path.join(root, "node", "BalineseDate.js"));

for (const value of fs.readFileSync(0, "utf8").trim().split(/\n/)) {
  if (!value) continue;
  const [year, month, day] = value.split("-").map(Number);
  const result = new BalineseDate(new Date(year, month - 1, day));
  const record = {
    date: value,
    pawukon_position_zero_based: result.wuku.id * 7 + result.saptaWara.id,
    wuku_index_zero_based: result.wuku.id,
    wuku_name: result.wuku.name,
    pancawara_native_index: result.pancaWara.id,
    pancawara_name: result.pancaWara.name,
    saptawara_native_index: result.saptaWara.id,
    saptawara_name: result.saptaWara.name,
    triwara_native_index: result.triWara.id,
    triwara_name: result.triWara.name,
    sadwara_native_index: result.sadWara.id,
    sadwara_name: result.sadWara.name,
  };
  process.stdout.write(JSON.stringify(record) + "\n");
}
