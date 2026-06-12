const fs = require("fs");

const pages = JSON.parse(fs.readFileSync("output/pages.json", "utf8"));

const urls = pages
  .map(p => `<url><loc>https://dans-place.com/${p.file}</loc></url>`)
  .join("\n");

const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset>
${urls}
</urlset>`;

fs.writeFileSync("output/sitemap.xml", xml);

console.log("SITEMAP_DONE");
