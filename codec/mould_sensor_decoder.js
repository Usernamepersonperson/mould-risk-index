// Uplink decoder for the 7-byte temperature / humidity payload (see mould_risk/sensors.py).
// Works as a ChirpStack v4 / LoRaWAN network-server codec: decodeUplink({bytes, fPort}).
//
//   byte 0     version (high nibble, must be 1) | flags (bit0 low battery, bit1 sensor fault)
//   bytes 1-2  temperature int16 BE, 0.01 C   (0x8000 = invalid)
//   bytes 3-4  humidity uint16 BE, 0.01 %     (0xFFFF = invalid)
//   byte 5     battery, 2.00 V + 0.01 V * value
//   byte 6     frame counter (wraps at 256)

function decodeUplink(input) {
  var b = input.bytes;
  if (!b || b.length !== 7) {
    return { data: {}, warnings: [], errors: ["expected 7 bytes, got " + (b ? b.length : 0)] };
  }
  var version = b[0] >> 4;
  if (version !== 1) {
    return { data: {}, warnings: [], errors: ["unsupported payload version " + version] };
  }
  var warnings = [];
  var tRaw = (b[1] << 8) | b[2];
  if (tRaw & 0x8000) tRaw -= 0x10000;
  var rhRaw = (b[3] << 8) | b[4];
  var data = {
    temperature_c: tRaw === -32768 ? null : tRaw / 100,
    humidity_pct: rhRaw === 0xffff ? null : rhRaw / 100,
    battery_v: 2 + b[5] / 100,
    counter: b[6],
    low_battery: (b[0] & 0x1) !== 0,
    fault: (b[0] & 0x2) !== 0,
  };
  if (rhRaw !== 0xffff && rhRaw > 10000) {
    return { data: {}, warnings: [], errors: ["humidity above 100 %"] };
  }
  if (data.low_battery) warnings.push("low battery");
  if (data.fault) warnings.push("sensor fault flag set");
  return { data: data, warnings: warnings, errors: [] };
}

// TTN / The Things Stack alias
function decodeUplinkTTN(input) {
  return decodeUplink(input);
}

if (typeof module !== "undefined") {
  module.exports = { decodeUplink: decodeUplink, decodeUplinkTTN: decodeUplinkTTN };
}
