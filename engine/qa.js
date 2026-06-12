function score(page) {
  let s = 10;
  if (page.length < 400) s -= 2;
  if (page.includes("maybe")) s -= 2;
  if (page.includes("possibly")) s -= 1;
  return s;
}
function isValid(page) {
  return score(page) >= 8;
}
module.exports = { score, isValid };
