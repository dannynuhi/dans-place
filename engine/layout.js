function layout({ title, description, content }) {
  return `
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <title>${title}</title>
  <meta name="description" content="${description}">

  <link rel="stylesheet" href="/site/design-system.css">
</head>

<body>
  <div class="container">

    <div class="card">
      <h1>${title}</h1>
      <p class="muted">${description}</p>
    </div>

    <div class="ad-slot">AD SLOT</div>

    <div class="card">
      ${content}
    </div>

    <div class="ad-slot">AD SLOT</div>

  </div>
</body>
</html>
`;
}

module.exports = { layout };
