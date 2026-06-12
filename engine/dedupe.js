const seen = new Set();
function isDuplicate(id) {
  if (seen.has(id)) return true;
  seen.add(id);
  return false;
}
module.exports = { isDuplicate };
