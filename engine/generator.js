function generatePage(seed) {
  return `
# ${seed.s} ${seed.p} issue

## Problem
Issue occurs in ${seed.s} during ${seed.c}.

## Fix
1. Restart
2. Check settings
3. Update software
4. Clear cache
5. Reinstall if needed

## If it continues
Check system conflicts or network issues.
`;
}
module.exports = { generatePage };
