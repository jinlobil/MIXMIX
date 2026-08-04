const major = Number(process.versions.node.split('.')[0]);
if (!Number.isInteger(major) || major < 18) {
  console.error(`Node.js 18+ required (found ${process.version})`);
  process.exit(1);
}
console.log(`Node.js ${process.version} OK`);
