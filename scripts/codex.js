const { execSync } = require("child_process");

function run(cmd) {
  execSync(cmd, { stdio: "inherit" });
}

console.log("CODEX START");

run("node scripts/run.js");
run("node scripts/sitemap.js");

console.log("CODEX DONE");
