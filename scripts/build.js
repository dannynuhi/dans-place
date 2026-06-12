const { execSync } = require("child_process");

execSync("node scripts/run.js", { stdio: "inherit" });

console.log("BUILD_OK");
