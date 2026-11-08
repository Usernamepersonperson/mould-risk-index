// usage: node codec/decode_hex.js 1109c4 ...  -> prints the decodeUplink() result as JSON
const { decodeUplink } = require("./mould_sensor_decoder.js");
const hex = process.argv[2] || "";
const bytes = hex.match(/../g) ? hex.match(/../g).map((h) => parseInt(h, 16)) : [];
console.log(JSON.stringify(decodeUplink({ bytes: bytes, fPort: 1 })));
