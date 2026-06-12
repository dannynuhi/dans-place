const { execSync } = require("child_process");

execSync("node scripts/validate.js", { stdio: "inherit" });
execSync("node scripts/orchestrate.js", { stdio: "inherit" });
execSync("node scripts/sitemap.js", { stdio: "inherit" });

console.log("BUILD_OK");
