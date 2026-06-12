const fs = require("fs");

function fail(msg) {
  console.error("VALIDATION FAILED:", msg);
  process.exit(1);
}

// 1. index must exist
if (!fs.existsSync("index.html")) {
  fail("missing index.html");
}

// 2. pages directory must exist
if (!fs.existsSync("pages")) {
  fail("missing pages/");
}

// 3. must contain at least 1 html page
const pages = fs.readdirSync("pages").filter(f => f.endsWith(".html"));
if (pages.length < 1) {
  fail("no html pages found");
}

// 4. structural lock must exist
if (!fs.existsSync(".structure-lock.json")) {
  fail("missing structure lock");
}

console.log("VALIDATION OK");
