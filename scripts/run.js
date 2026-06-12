const { execSync } = require("child_process");

function step(cmd) {
  execSync(cmd, { stdio: "inherit" });
}

console.log("START PIPELINE");

step("node scripts/orchestrate.js");
step("node scripts/sitemap.js");

console.log("DONE PIPELINE");
